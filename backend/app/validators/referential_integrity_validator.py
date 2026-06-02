"""Referential Integrity Validator for PySpark DataFrames.

Validates:
- Primary key uniqueness (no duplicate primary key values)
- Foreign key references (all foreign key values exist in parent dataset)
- Detects orphan records with missing parent references
"""

import time
from typing import Dict, List, Optional, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, collect_list, struct, to_json, lit
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class ReferentialIntegrityValidator(BaseValidator):
    """
    Validates referential integrity constraints on DataFrames.
    
    Checks for:
    - Primary key uniqueness (duplicate detection)
    - Foreign key validity (orphan record detection)
    - Failed row extraction for detailed analysis
    """
    
    def __init__(
        self,
        primary_key_columns: Optional[List[str]] = None,
        foreign_key_mappings: Optional[Dict[str, tuple]] = None,
        name: str = "ReferentialIntegrityValidator"
    ):
        """
        Initialize referential integrity validator.
        
        Args:
            primary_key_columns: List of columns that form the primary key
            foreign_key_mappings: Dict mapping foreign key column to (parent_df, parent_key_column)
                                  Example: {'customer_id': (customers_df, 'id')}
            name: Validator name
        """
        super().__init__(name)
        self.primary_key_columns = primary_key_columns or []
        self.foreign_key_mappings = foreign_key_mappings or {}
        
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate referential integrity constraints.
        
        Args:
            df: DataFrame to validate
            **kwargs: Additional parameters
                - parent_datasets: Dict[str, DataFrame] for foreign key validation
            
        Returns:
            ValidationResult with integrity validation details
        """
        start_time = time.time()
        errors = []
        details = {}
        total_records = df.count()
        failed_records = 0
        
        try:
            # Validate primary key uniqueness if configured
            if self.primary_key_columns:
                pk_result = self._validate_primary_key_uniqueness(df)
                details['primary_key_validation'] = pk_result
                failed_records += pk_result.get('duplicate_count', 0)
                
                if pk_result.get('has_duplicates', False):
                    errors.append(
                        f"Found {pk_result['duplicate_count']} duplicate primary key value(s) "
                        f"in columns: {', '.join(self.primary_key_columns)}"
                    )
            
            # Validate foreign key references if configured
            parent_datasets = kwargs.get('parent_datasets', {})
            if self.foreign_key_mappings and parent_datasets:
                fk_results = self._validate_foreign_keys(df, parent_datasets)
                details['foreign_key_validation'] = fk_results
                
                for fk_name, fk_result in fk_results.items():
                    orphan_count = fk_result.get('orphan_count', 0)
                    failed_records += orphan_count
                    
                    if orphan_count > 0:
                        errors.append(
                            f"Found {orphan_count} orphan record(s) with invalid "
                            f"foreign key '{fk_name}'"
                        )
            
            # Determine overall status
            if errors:
                status = ValidationStatus.FAILED
                passed = False
                message = f"Referential integrity validation failed with {len(errors)} issue(s)"
            else:
                status = ValidationStatus.PASSED
                passed = True
                message = "All referential integrity checks passed"
            
            # Calculate pass rate
            pass_rate = ((total_records - failed_records) / total_records * 100) if total_records > 0 else 100.0
            
            execution_time = (time.time() - start_time) * 1000
            
            return ValidationResult(
                validator_name=self.name,
                status=status,
                passed=passed,
                total_records=total_records,
                failed_records=failed_records,
                pass_rate=pass_rate,
                message=message,
                details=details,
                errors=errors,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ValidationResult(
                validator_name=self.name,
                status=ValidationStatus.ERROR,
                passed=False,
                total_records=total_records,
                failed_records=0,
                pass_rate=0.0,
                message=f"Validation error: {str(e)}",
                details={},
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def _validate_primary_key_uniqueness(self, df: DataFrame) -> Dict[str, Any]:
        """
        Validate primary key uniqueness and detect duplicates.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results including duplicate information
        """
        if not self.primary_key_columns:
            return {
                'has_duplicates': False,
                'duplicate_count': 0,
                'duplicate_keys': []
            }
        
        # Group by primary key columns and count occurrences
        grouped = df.groupBy(*self.primary_key_columns).agg(
            count(lit(1)).alias('occurrence_count')
        )
        
        # Find duplicates (occurrence_count > 1)
        duplicates = grouped.filter(col('occurrence_count') > 1)
        duplicate_count_total = duplicates.agg(
            {'occurrence_count': 'sum'}
        ).collect()[0][0]
        
        # If no duplicates, return early
        if duplicate_count_total is None:
            duplicate_count_total = 0
            
        has_duplicates = duplicate_count_total > 0
        
        # Extract duplicate key values (limit to first 100 for performance)
        duplicate_keys = []
        if has_duplicates:
            duplicate_rows = duplicates.limit(100).collect()
            for row in duplicate_rows:
                key_values = {col_name: row[col_name] for col_name in self.primary_key_columns}
                key_values['occurrence_count'] = row['occurrence_count']
                duplicate_keys.append(key_values)
        
        # Calculate actual duplicate record count (total occurrences - unique keys)
        duplicate_record_count = duplicate_count_total - duplicates.count() if has_duplicates else 0
        
        return {
            'has_duplicates': has_duplicates,
            'duplicate_count': duplicate_record_count,
            'unique_duplicate_keys': duplicates.count() if has_duplicates else 0,
            'duplicate_keys': duplicate_keys
        }
    
    def _validate_foreign_keys(
        self,
        df: DataFrame,
        parent_datasets: Dict[str, DataFrame]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate foreign key references against parent datasets.
        
        Args:
            df: Child DataFrame to validate
            parent_datasets: Dict mapping dataset names to parent DataFrames
            
        Returns:
            Dict with validation results for each foreign key
        """
        results = {}
        
        for fk_column, (parent_dataset_name, parent_key_column) in self.foreign_key_mappings.items():
            if fk_column not in df.columns:
                results[fk_column] = {
                    'valid': False,
                    'orphan_count': 0,
                    'error': f"Foreign key column '{fk_column}' not found in dataset"
                }
                continue
            
            # Get parent dataset
            parent_df = parent_datasets.get(parent_dataset_name)
            if parent_df is None:
                results[fk_column] = {
                    'valid': False,
                    'orphan_count': 0,
                    'error': f"Parent dataset '{parent_dataset_name}' not provided"
                }
                continue
            
            if parent_key_column not in parent_df.columns:
                results[fk_column] = {
                    'valid': False,
                    'orphan_count': 0,
                    'error': f"Parent key column '{parent_key_column}' not found in parent dataset"
                }
                continue
            
            # Find orphan records (foreign key values not in parent)
            orphans = df.join(
                parent_df.select(col(parent_key_column)),
                df[fk_column] == parent_df[parent_key_column],
                'left_anti'  # Returns rows from df that don't match parent_df
            )
            
            orphan_count = orphans.count()
            
            # Extract sample orphan values (limit to first 100)
            orphan_values = []
            if orphan_count > 0:
                orphan_rows = orphans.select(fk_column).distinct().limit(100).collect()
                orphan_values = [row[fk_column] for row in orphan_rows]
            
            results[fk_column] = {
                'valid': orphan_count == 0,
                'orphan_count': orphan_count,
                'parent_dataset': parent_dataset_name,
                'parent_key_column': parent_key_column,
                'orphan_values': orphan_values
            }
        
        return results
    
    def extract_failed_rows(
        self,
        df: DataFrame,
        validation_type: str = 'all',
        parent_datasets: Optional[Dict[str, DataFrame]] = None
    ) -> DataFrame:
        """
        Extract rows that failed integrity validation.
        
        Args:
            df: DataFrame to extract failed rows from
            validation_type: Type of validation ('primary_key', 'foreign_key', or 'all')
            parent_datasets: Dict of parent datasets for foreign key validation
            
        Returns:
            DataFrame containing only the failed rows with validation metadata
        """
        failed_dfs = []
        
        # Extract primary key duplicate rows
        if validation_type in ('primary_key', 'all') and self.primary_key_columns:
            duplicate_df = self._extract_duplicate_primary_key_rows(df)
            if duplicate_df.count() > 0:
                failed_dfs.append(
                    duplicate_df.withColumn('validation_failure_type', lit('duplicate_primary_key'))
                )
        
        # Extract foreign key orphan rows
        if validation_type in ('foreign_key', 'all') and self.foreign_key_mappings and parent_datasets:
            orphan_df = self._extract_orphan_foreign_key_rows(df, parent_datasets)
            if orphan_df.count() > 0:
                failed_dfs.append(
                    orphan_df.withColumn('validation_failure_type', lit('orphan_foreign_key'))
                )
        
        # Union all failed DataFrames
        if failed_dfs:
            return failed_dfs[0].unionByName(*failed_dfs[1:], allowMissingColumns=True) if len(failed_dfs) > 1 else failed_dfs[0]
        else:
            # Return empty DataFrame with same schema plus validation metadata
            return df.limit(0).withColumn('validation_failure_type', lit(''))
    
    def _extract_duplicate_primary_key_rows(self, df: DataFrame) -> DataFrame:
        """
        Extract rows with duplicate primary key values.
        
        Args:
            df: DataFrame to extract from
            
        Returns:
            DataFrame containing duplicate rows with occurrence count
        """
        if not self.primary_key_columns:
            return df.limit(0)
        
        # Count occurrences of each primary key
        key_counts = df.groupBy(*self.primary_key_columns).agg(
            count(lit(1)).alias('_pk_occurrence_count')
        )
        
        # Filter for duplicates (count > 1)
        duplicate_keys = key_counts.filter(col('_pk_occurrence_count') > 1)
        
        # Join back to get full rows with duplicates
        duplicates = df.join(
            duplicate_keys,
            on=self.primary_key_columns,
            how='inner'
        )
        
        return duplicates
    
    def _extract_orphan_foreign_key_rows(
        self,
        df: DataFrame,
        parent_datasets: Dict[str, DataFrame]
    ) -> DataFrame:
        """
        Extract rows with invalid foreign key references (orphans).
        
        Args:
            df: Child DataFrame to extract from
            parent_datasets: Dict of parent datasets
            
        Returns:
            DataFrame containing orphan rows with FK metadata
        """
        orphan_dfs = []
        
        for fk_column, (parent_dataset_name, parent_key_column) in self.foreign_key_mappings.items():
            if fk_column not in df.columns:
                continue
            
            parent_df = parent_datasets.get(parent_dataset_name)
            if parent_df is None or parent_key_column not in parent_df.columns:
                continue
            
            # Find orphan records using left anti join
            orphans = df.join(
                parent_df.select(col(parent_key_column)),
                df[fk_column] == parent_df[parent_key_column],
                'left_anti'
            )
            
            if orphans.count() > 0:
                orphans = orphans.withColumn('_invalid_fk_column', lit(fk_column))
                orphan_dfs.append(orphans)
        
        # Union all orphan DataFrames
        if orphan_dfs:
            return orphan_dfs[0].unionByName(*orphan_dfs[1:], allowMissingColumns=True) if len(orphan_dfs) > 1 else orphan_dfs[0]
        else:
            return df.limit(0)


def detect_duplicates(df: DataFrame, key_columns: List[str]) -> Dict[str, Any]:
    """
    Utility function to detect duplicate records based on key columns.
    
    Args:
        df: DataFrame to check for duplicates
        key_columns: List of column names that form the key
        
    Returns:
        Dict containing:
            - total_records: Total number of records
            - unique_records: Number of unique key combinations
            - duplicate_count: Number of duplicate records
            - has_duplicates: Boolean indicating if duplicates exist
            - duplicate_keys: List of duplicate key values (limited to 100)
    """
    if not key_columns:
        return {
            'total_records': df.count(),
            'unique_records': df.count(),
            'duplicate_count': 0,
            'has_duplicates': False,
            'duplicate_keys': []
        }
    
    total_records = df.count()
    
    # Count unique key combinations
    unique_records = df.select(*key_columns).distinct().count()
    
    # Calculate duplicates
    duplicate_count = total_records - unique_records
    has_duplicates = duplicate_count > 0
    
    # Extract duplicate key values
    duplicate_keys = []
    if has_duplicates:
        key_counts = df.groupBy(*key_columns).agg(
            count(lit(1)).alias('count')
        ).filter(col('count') > 1)
        
        duplicate_rows = key_counts.limit(100).collect()
        for row in duplicate_rows:
            key_values = {col_name: row[col_name] for col_name in key_columns}
            key_values['count'] = row['count']
            duplicate_keys.append(key_values)
    
    return {
        'total_records': total_records,
        'unique_records': unique_records,
        'duplicate_count': duplicate_count,
        'has_duplicates': has_duplicates,
        'duplicate_keys': duplicate_keys
    }


def extract_failed_rows(
    df: DataFrame,
    condition_column: str,
    expected_value: Any = True
) -> DataFrame:
    """
    Utility function to extract rows that failed a validation condition.
    
    Args:
        df: DataFrame to filter
        condition_column: Name of the boolean column indicating pass/fail
        expected_value: Expected value for passing rows (default: True)
        
    Returns:
        DataFrame containing only rows where condition_column != expected_value
    """
    return df.filter(col(condition_column) != expected_value)
