"""Checksum validation for data integrity verification."""

import time
import hashlib
from typing import Dict, List, Optional
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class ChecksumValidator(BaseValidator):
    """
    Validates data integrity using checksums.
    
    Performs:
    - Row-level checksum validation
    - Column-level checksum validation
    - Dataset-level checksum comparison
    - Duplicate detection via checksum
    """
    
    def __init__(
        self,
        expected_checksum: Optional[str] = None,
        checksum_columns: Optional[List[str]] = None,
        detect_duplicates: bool = False,
        name: str = "ChecksumValidator"
    ):
        """
        Initialize checksum validator.
        
        Args:
            expected_checksum: Expected dataset checksum (MD5 hash)
            checksum_columns: Columns to include in checksum calculation
            detect_duplicates: Whether to detect duplicate rows via checksum
            name: Validator name
        """
        super().__init__(name)
        self.expected_checksum = expected_checksum
        self.checksum_columns = checksum_columns
        self.detect_duplicates = detect_duplicates
    
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate data integrity using checksums.
        
        Args:
            df: DataFrame to validate
            **kwargs: Optional parameters:
                - algorithm: Hash algorithm ('md5', 'sha256') - default 'md5'
            
        Returns:
            ValidationResult with checksum validation details
        """
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            total_records = df.count()
            
            if total_records == 0:
                return self._create_result(
                    status=ValidationStatus.WARNING,
                    passed=False,
                    total_records=0,
                    message="Cannot validate checksums: DataFrame is empty",
                    execution_time_ms=round((time.time() - start_time) * 1000, 2)
                )
            
            algorithm = kwargs.get('algorithm', 'md5')
            
            # Determine columns to checksum
            columns_to_hash = self.checksum_columns or df.columns
            
            # Validate columns exist
            missing_cols = set(columns_to_hash) - set(df.columns)
            if missing_cols:
                errors.append(f"Checksum columns not found: {', '.join(missing_cols)}")
                columns_to_hash = [c for c in columns_to_hash if c in df.columns]
            
            if not columns_to_hash:
                return self._create_result(
                    status=ValidationStatus.ERROR,
                    passed=False,
                    message="No valid columns for checksum calculation",
                    errors=errors,
                    execution_time_ms=round((time.time() - start_time) * 1000, 2)
                )
            
            # Add row-level checksum column
            df_with_checksum = self._add_row_checksum(df, columns_to_hash, algorithm)
            
            # Detect duplicates if enabled
            if self.detect_duplicates:
                duplicate_count = df_with_checksum.groupBy("_row_checksum").count().filter(F.col("count") > 1).count()
                details["duplicate_count"] = duplicate_count
                
                if duplicate_count > 0:
                    errors.append(f"Found {duplicate_count} duplicate row(s) based on checksum")
            
            # Calculate dataset-level checksum
            dataset_checksum = self._calculate_dataset_checksum(df_with_checksum, algorithm)
            details["dataset_checksum"] = dataset_checksum
            details["checksum_algorithm"] = algorithm
            details["checksum_columns"] = columns_to_hash
            
            # Compare with expected checksum if provided
            if self.expected_checksum:
                if dataset_checksum != self.expected_checksum:
                    errors.append(
                        f"Dataset checksum mismatch: expected '{self.expected_checksum}', "
                        f"got '{dataset_checksum}'"
                    )
                details["expected_checksum"] = self.expected_checksum
                details["checksum_match"] = dataset_checksum == self.expected_checksum
            
            # Calculate column-level checksums
            column_checksums = self._calculate_column_checksums(df, columns_to_hash, algorithm)
            details["column_checksums"] = column_checksums
            
            # Determine validation status
            passed = len(errors) == 0
            status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
            
            if passed:
                message = f"Checksum validation passed (algorithm: {algorithm})"
            else:
                message = f"Checksum validation failed: {len(errors)} issue(s) found"
            
            execution_time = (time.time() - start_time) * 1000
            
            return self._create_result(
                status=status,
                passed=passed,
                total_records=total_records,
                failed_records=details.get("duplicate_count", 0),
                message=message,
                details=details,
                errors=errors,
                execution_time_ms=round(execution_time, 2)
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self._create_result(
                status=ValidationStatus.ERROR,
                passed=False,
                message=f"Checksum validation error: {str(e)}",
                errors=[str(e)],
                execution_time_ms=round(execution_time, 2)
            )
    
    def _add_row_checksum(self, df: DataFrame, columns: List[str], algorithm: str) -> DataFrame:
        """
        Add a checksum column to each row.
        
        Args:
            df: Input DataFrame
            columns: Columns to include in checksum
            algorithm: Hash algorithm
            
        Returns:
            DataFrame with '_row_checksum' column added
        """
        # Concatenate columns and calculate hash
        concat_expr = F.concat_ws("|", *[F.coalesce(F.col(c).cast("string"), F.lit("NULL")) for c in columns])
        
        if algorithm == 'md5':
            checksum_expr = F.md5(concat_expr)
        elif algorithm == 'sha256':
            checksum_expr = F.sha2(concat_expr, 256)
        else:
            checksum_expr = F.md5(concat_expr)  # Default to MD5
        
        return df.withColumn("_row_checksum", checksum_expr)
    
    def _calculate_dataset_checksum(self, df_with_checksum: DataFrame, algorithm: str) -> str:
        """
        Calculate a single checksum for the entire dataset.
        
        Args:
            df_with_checksum: DataFrame with row checksums
            algorithm: Hash algorithm
            
        Returns:
            Dataset checksum string
        """
        # Collect all row checksums, sort them, and hash the result
        row_checksums = df_with_checksum.select("_row_checksum").rdd.flatMap(lambda x: x).collect()
        row_checksums.sort()
        
        combined = "|".join(row_checksums)
        
        if algorithm == 'md5':
            return hashlib.md5(combined.encode()).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(combined.encode()).hexdigest()
        else:
            return hashlib.md5(combined.encode()).hexdigest()
    
    def _calculate_column_checksums(self, df: DataFrame, columns: List[str], algorithm: str) -> Dict[str, str]:
        """
        Calculate checksum for each column.
        
        Args:
            df: Input DataFrame
            columns: Columns to checksum
            algorithm: Hash algorithm
            
        Returns:
            Dictionary mapping column names to checksums
        """
        column_checksums = {}
        
        for col in columns:
            # Get all values, sort, and hash
            values = df.select(col).rdd.flatMap(lambda x: [str(x[0]) if x[0] is not None else "NULL"]).collect()
            values.sort()
            
            combined = "|".join(values)
            
            if algorithm == 'md5':
                col_checksum = hashlib.md5(combined.encode()).hexdigest()
            elif algorithm == 'sha256':
                col_checksum = hashlib.sha256(combined.encode()).hexdigest()
            else:
                col_checksum = hashlib.md5(combined.encode()).hexdigest()
            
            column_checksums[col] = col_checksum
        
        return column_checksums
