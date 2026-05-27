"""Schema validation for PySpark DataFrames."""

import time
from typing import Dict, List, Optional, Set
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, DataType
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class SchemaValidator(BaseValidator):
    """
    Validates DataFrame schema against expected column definitions.
    
    Checks for:
    - Required columns presence
    - Column data types
    - Extra or missing columns
    """
    
    def __init__(
        self,
        expected_schema: Optional[StructType] = None,
        required_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, str]] = None,
        name: str = "SchemaValidator"
    ):
        """
        Initialize schema validator.
        
        Args:
            expected_schema: Complete expected StructType schema
            required_columns: List of required column names
            column_types: Dict mapping column names to expected type strings
            name: Validator name
        """
        super().__init__(name)
        self.expected_schema = expected_schema
        self.required_columns = set(required_columns or [])
        self.column_types = column_types or {}
    
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate DataFrame schema.
        
        Args:
            df: DataFrame to validate
            **kwargs: Additional parameters (unused)
            
        Returns:
            ValidationResult with schema validation details
        """
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            actual_columns = set(df.columns)
            actual_schema = df.schema
            
            # Check for missing required columns
            missing_columns = self.required_columns - actual_columns
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(sorted(missing_columns))}")
            
            # Check for extra columns (if expected_schema is provided)
            if self.expected_schema:
                expected_columns = set(self.expected_schema.fieldNames())
                extra_columns = actual_columns - expected_columns
                if extra_columns:
                    details["extra_columns"] = sorted(list(extra_columns))
            
            # Validate column types
            type_mismatches = []
            for col_name, expected_type in self.column_types.items():
                if col_name in actual_columns:
                    actual_type = [f.dataType.simpleString() for f in actual_schema.fields if f.name == col_name][0]
                    if actual_type != expected_type:
                        type_mismatches.append({
                            "column": col_name,
                            "expected": expected_type,
                            "actual": actual_type
                        })
            
            if type_mismatches:
                errors.append(f"Type mismatches found in {len(type_mismatches)} column(s)")
                details["type_mismatches"] = type_mismatches
            
            # Store schema information
            details["actual_columns"] = sorted(list(actual_columns))
            details["column_count"] = len(actual_columns)
            details["schema"] = {f.name: f.dataType.simpleString() for f in actual_schema.fields}
            
            # Determine validation status
            passed = len(errors) == 0
            status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
            
            message = "Schema validation passed" if passed else f"Schema validation failed: {len(errors)} issue(s) found"
            
            execution_time = (time.time() - start_time) * 1000
            
            # Try to count records, but don't fail if it errors (Windows PySpark issue)
            total_records = 0
            try:
                if passed:
                    total_records = df.count()
            except Exception:
                # Counting may fail on Windows due to worker issues, but schema validation succeeded
                pass
            
            return self._create_result(
                status=status,
                passed=passed,
                total_records=total_records,
                failed_records=0,
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
                message=f"Schema validation error: {str(e)}",
                errors=[str(e)],
                execution_time_ms=round(execution_time, 2)
            )
