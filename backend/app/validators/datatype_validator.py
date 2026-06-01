"""Data type validation for PySpark DataFrames."""

import time
from typing import Dict, List, Optional
from datetime import datetime as dt
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StringType, IntegerType, LongType, FloatType, DoubleType,
    BooleanType, DateType, TimestampType, DecimalType
)
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class DatatypeValidator(BaseValidator):
    """
    Validates data types and type-specific rules for DataFrame columns.
    
    Checks for:
    - Type conformity (values match expected type)
    - String pattern validation
    - Numeric range validation
    - Boolean value validation
    - Date format validation
    """
    
    def __init__(
        self,
        column_types: Optional[Dict[str, str]] = None,
        string_patterns: Optional[Dict[str, str]] = None,
        numeric_ranges: Optional[Dict[str, tuple]] = None,
        name: str = "DatatypeValidator"
    ):
        """
        Initialize datatype validator.
        
        Args:
            column_types: Dict mapping column names to expected type strings
                          ('string', 'integer', 'float', 'boolean', 'date')
            string_patterns: Dict mapping column names to regex patterns
            numeric_ranges: Dict mapping column names to (min, max) tuples
            name: Validator name
        """
        super().__init__(name)
        self.column_types = column_types or {}
        self.string_patterns = string_patterns or {}
        self.numeric_ranges = numeric_ranges or {}
    
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate data types in DataFrame.
        
        Args:
            df: DataFrame to validate
            **kwargs: Additional parameters
            
        Returns:
            ValidationResult with datatype validation details
        """
        start_time = time.time()
        errors = []
        details = {}
        failed_count = 0
        total_count = df.count()
        
        try:
            # Validate each column's data type
            for column_name, expected_type in self.column_types.items():
                if column_name not in df.columns:
                    errors.append(f"Column '{column_name}' not found in DataFrame")
                    continue
                
                # Get actual type
                actual_type = dict(df.dtypes)[column_name]
                type_details = self._validate_column_type(
                    df, column_name, expected_type, actual_type
                )
                details[column_name] = type_details
                
                # Count type mismatches
                if type_details.get('type_mismatch_count', 0) > 0:
                    failed_count += type_details['type_mismatch_count']
            
            # Additional string pattern validation
            for column_name, pattern in self.string_patterns.items():
                if column_name in df.columns:
                    pattern_result = self._validate_string_pattern(
                        df, column_name, pattern
                    )
                    if column_name in details:
                        details[column_name].update(pattern_result)
                    else:
                        details[column_name] = pattern_result
                    
                    if pattern_result.get('pattern_mismatch_count', 0) > 0:
                        failed_count += pattern_result['pattern_mismatch_count']
            
            # Additional numeric range validation
            for column_name, (min_val, max_val) in self.numeric_ranges.items():
                if column_name in df.columns:
                    range_result = self._validate_numeric_range(
                        df, column_name, min_val, max_val
                    )
                    if column_name in details:
                        details[column_name].update(range_result)
                    else:
                        details[column_name] = range_result
                    
                    if range_result.get('out_of_range_count', 0) > 0:
                        failed_count += range_result['out_of_range_count']
            
            # Determine validation status
            pass_rate = ((total_count - failed_count) / total_count * 100) if total_count > 0 else 100.0
            
            if failed_count == 0:
                status = ValidationStatus.PASSED
                message = "All datatype validations passed"
                passed = True
            elif pass_rate >= 95:
                status = ValidationStatus.WARNING
                message = f"{failed_count} records failed datatype validation"
                passed = False
            else:
                status = ValidationStatus.FAILED
                message = f"{failed_count} records failed datatype validation"
                passed = False
            
            execution_time = (time.time() - start_time) * 1000
            
            return ValidationResult(
                validator_name=self.name,
                status=status,
                passed=passed,
                total_records=total_count,
                failed_records=failed_count,
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
                total_records=total_count,
                failed_records=total_count,
                pass_rate=0.0,
                message=f"Datatype validation error: {str(e)}",
                details=details,
                errors=[str(e)],
                execution_time_ms=execution_time
            )
    
    def _validate_column_type(
        self,
        df: DataFrame,
        column_name: str,
        expected_type: str,
        actual_type: str
    ) -> Dict:
        """Validate a single column's data type."""
        result = {
            'expected_type': expected_type,
            'actual_type': actual_type,
            'type_mismatch_count': 0
        }
        
        # Map expected types to PySpark types
        type_mapping = {
            'string': ['string'],
            'integer': ['int', 'bigint', 'smallint', 'tinyint', 'long'],
            'float': ['float', 'double', 'decimal'],
            'boolean': ['boolean'],
            'date': ['date', 'timestamp']
        }
        
        # Check if actual type matches expected type
        expected_spark_types = type_mapping.get(expected_type.lower(), [])
        is_type_match = any(t in actual_type.lower() for t in expected_spark_types)
        
        result['type_matches'] = is_type_match
        
        if not is_type_match:
            # Count rows that would fail type casting
            try:
                if expected_type.lower() == 'integer':
                    mismatch_count = df.filter(
                        F.col(column_name).isNotNull() &
                        (~F.col(column_name).cast(LongType()).isNotNull())
                    ).count()
                elif expected_type.lower() == 'float':
                    mismatch_count = df.filter(
                        F.col(column_name).isNotNull() &
                        (~F.col(column_name).cast(DoubleType()).isNotNull())
                    ).count()
                elif expected_type.lower() == 'boolean':
                    mismatch_count = df.filter(
                        F.col(column_name).isNotNull() &
                        (~F.col(column_name).isin(['true', 'false', '1', '0', 'True', 'False']))
                    ).count()
                elif expected_type.lower() == 'date':
                    mismatch_count = df.filter(
                        F.col(column_name).isNotNull() &
                        (~F.col(column_name).cast(DateType()).isNotNull())
                    ).count()
                else:
                    mismatch_count = 0
                
                result['type_mismatch_count'] = mismatch_count
            except Exception:
                result['type_mismatch_count'] = 0
        
        return result
    
    def _validate_string_pattern(
        self,
        df: DataFrame,
        column_name: str,
        pattern: str
    ) -> Dict:
        """Validate string column against regex pattern."""
        result = {
            'pattern': pattern,
            'pattern_mismatch_count': 0
        }
        
        try:
            # Count rows that don't match the pattern
            mismatch_count = df.filter(
                F.col(column_name).isNotNull() &
                (~F.col(column_name).rlike(pattern))
            ).count()
            
            result['pattern_mismatch_count'] = mismatch_count
            
        except Exception as e:
            result['pattern_error'] = str(e)
        
        return result
    
    def _validate_numeric_range(
        self,
        df: DataFrame,
        column_name: str,
        min_val: float,
        max_val: float
    ) -> Dict:
        """Validate numeric column is within specified range."""
        result = {
            'min_value': min_val,
            'max_value': max_val,
            'out_of_range_count': 0
        }
        
        try:
            # Count rows outside the range
            out_of_range = df.filter(
                F.col(column_name).isNotNull() &
                ((F.col(column_name) < min_val) | (F.col(column_name) > max_val))
            ).count()
            
            result['out_of_range_count'] = out_of_range
            
            # Get actual min/max for comparison
            stats = df.agg(
                F.min(column_name).alias('actual_min'),
                F.max(column_name).alias('actual_max')
            ).collect()[0]
            
            result['actual_min'] = stats['actual_min']
            result['actual_max'] = stats['actual_max']
            
        except Exception as e:
            result['range_error'] = str(e)
        
        return result
