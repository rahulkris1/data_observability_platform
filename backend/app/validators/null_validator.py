"""Null/missing value validation for PySpark DataFrames."""

import time
from typing import Dict, List, Optional
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class NullValidator(BaseValidator):
    """
    Validates null/missing values in DataFrame columns.
    
    Checks for:
    - Null values in specified columns
    - Null percentage thresholds
    - Completely empty columns
    """
    
    def __init__(
        self,
        non_null_columns: Optional[List[str]] = None,
        max_null_percentage: float = 0.0,
        column_thresholds: Optional[Dict[str, float]] = None,
        name: str = "NullValidator"
    ):
        """
        Initialize null validator.
        
        Args:
            non_null_columns: Columns that must not contain any nulls
            max_null_percentage: Maximum allowed null percentage across all columns (0-100)
            column_thresholds: Dict mapping column names to max null percentage
            name: Validator name
        """
        super().__init__(name)
        self.non_null_columns = set(non_null_columns or [])
        self.max_null_percentage = max_null_percentage
        self.column_thresholds = column_thresholds or {}
    
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate null values in DataFrame.
        
        Args:
            df: DataFrame to validate
            **kwargs: Optional parameters:
                - columns: List of columns to check (default: all columns)
            
        Returns:
            ValidationResult with null validation details
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
                    message="Cannot validate nulls: DataFrame is empty",
                    execution_time_ms=round((time.time() - start_time) * 1000, 2)
                )
            
            # Determine which columns to check
            columns_to_check = kwargs.get('columns', df.columns)
            
            # Calculate null counts for each column
            null_counts = {}
            null_percentages = {}
            
            for col in columns_to_check:
                if col not in df.columns:
                    errors.append(f"Column '{col}' not found in DataFrame")
                    continue
                
                null_count = df.filter(F.col(col).isNull()).count()
                null_counts[col] = null_count
                null_percentages[col] = round((null_count / total_records) * 100, 2)
            
            # Check non-null columns
            for col in self.non_null_columns:
                if col in null_counts and null_counts[col] > 0:
                    errors.append(
                        f"Column '{col}' must not contain nulls, found {null_counts[col]} "
                        f"({null_percentages[col]}%)"
                    )
            
            # Check column-specific thresholds
            for col, threshold in self.column_thresholds.items():
                if col in null_percentages and null_percentages[col] > threshold:
                    errors.append(
                        f"Column '{col}' exceeds null threshold: {null_percentages[col]}% > {threshold}%"
                    )
            
            # Check global max null percentage
            if self.max_null_percentage > 0:
                for col, percentage in null_percentages.items():
                    if percentage > self.max_null_percentage:
                        errors.append(
                            f"Column '{col}' exceeds global null threshold: "
                            f"{percentage}% > {self.max_null_percentage}%"
                        )
            
            # Find completely empty columns
            empty_columns = [col for col, count in null_counts.items() if count == total_records]
            if empty_columns:
                details["empty_columns"] = empty_columns
                errors.append(f"Found {len(empty_columns)} completely empty column(s): {', '.join(empty_columns)}")
            
            # Store detailed null statistics
            details["null_counts"] = null_counts
            details["null_percentages"] = null_percentages
            details["total_records"] = total_records
            details["columns_checked"] = len(columns_to_check)
            
            # Calculate overall statistics
            total_null_values = sum(null_counts.values())
            total_cells = total_records * len(columns_to_check)
            overall_null_percentage = round((total_null_values / total_cells) * 100, 2) if total_cells > 0 else 0
            
            details["total_null_values"] = total_null_values
            details["overall_null_percentage"] = overall_null_percentage
            
            # Determine validation status
            passed = len(errors) == 0
            status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
            
            if passed:
                message = f"Null validation passed: {overall_null_percentage}% null values overall"
            else:
                message = f"Null validation failed: {len(errors)} issue(s) found"
            
            execution_time = (time.time() - start_time) * 1000
            
            return self._create_result(
                status=status,
                passed=passed,
                total_records=total_records,
                failed_records=total_null_values,
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
                message=f"Null validation error: {str(e)}",
                errors=[str(e)],
                execution_time_ms=round(execution_time, 2)
            )
