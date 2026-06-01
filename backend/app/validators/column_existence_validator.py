"""Column existence validation for PySpark DataFrames."""

import time
from typing import List, Optional, Set
from pyspark.sql import DataFrame
from app.validators.base_validator import BaseValidator, ValidationResult, ValidationStatus


class ColumnExistenceValidator(BaseValidator):
    """
    Validates that required columns exist in DataFrame against schema contracts.
    
    Checks for:
    - Presence of all required columns
    - Detection of missing columns
    - Detection of extra/unexpected columns
    - Column name case sensitivity
    """
    
    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        optional_columns: Optional[List[str]] = None,
        allow_extra_columns: bool = True,
        case_sensitive: bool = True,
        name: str = "ColumnExistenceValidator"
    ):
        """
        Initialize column existence validator.
        
        Args:
            required_columns: List of columns that must be present
            optional_columns: List of columns that may be present
            allow_extra_columns: Whether to allow columns not in required/optional lists
            case_sensitive: Whether column name matching is case-sensitive
            name: Validator name
        """
        super().__init__(name)
        self.required_columns = set(required_columns or [])
        self.optional_columns = set(optional_columns or [])
        self.allow_extra_columns = allow_extra_columns
        self.case_sensitive = case_sensitive
        
        # If not case sensitive, normalize to lowercase
        if not case_sensitive:
            self.required_columns = {col.lower() for col in self.required_columns}
            self.optional_columns = {col.lower() for col in self.optional_columns}
    
    def validate(self, df: DataFrame, **kwargs) -> ValidationResult:
        """
        Validate column existence in DataFrame.
        
        Args:
            df: DataFrame to validate
            **kwargs: Optional parameters:
                - schema_contract: Dict with 'required_columns' and 'optional_columns'
            
        Returns:
            ValidationResult with column existence validation details
        """
        start_time = time.time()
        errors = []
        details = {}
        
        try:
            # Override with schema contract if provided
            schema_contract = kwargs.get('schema_contract')
            if schema_contract:
                required_cols = set(schema_contract.get('required_columns', []))
                optional_cols = set(schema_contract.get('optional_columns', []))
            else:
                required_cols = self.required_columns
                optional_cols = self.optional_columns
            
            # Get actual columns from DataFrame
            actual_columns = set(df.columns)
            
            # Normalize case if needed
            if not self.case_sensitive:
                actual_columns = {col.lower() for col in actual_columns}
                required_cols = {col.lower() for col in required_cols}
                optional_cols = {col.lower() for col in optional_cols}
            
            # Find missing required columns
            missing_columns = required_cols - actual_columns
            
            # Find extra columns (not in required or optional)
            expected_columns = required_cols | optional_cols
            extra_columns = actual_columns - expected_columns if expected_columns else set()
            
            # Find present optional columns
            present_optional = optional_cols & actual_columns
            
            # Populate details
            details['required_columns'] = list(required_cols)
            details['optional_columns'] = list(optional_cols)
            details['actual_columns'] = list(actual_columns)
            details['missing_columns'] = list(missing_columns)
            details['extra_columns'] = list(extra_columns)
            details['present_optional_columns'] = list(present_optional)
            details['total_columns_expected'] = len(required_cols) + len(optional_cols)
            details['total_columns_actual'] = len(actual_columns)
            
            # Generate error messages
            if missing_columns:
                errors.append(
                    f"Missing {len(missing_columns)} required column(s): {', '.join(sorted(missing_columns))}"
                )
            
            if extra_columns and not self.allow_extra_columns:
                errors.append(
                    f"Found {len(extra_columns)} unexpected column(s): {', '.join(sorted(extra_columns))}"
                )
            
            # Determine validation status
            if missing_columns:
                status = ValidationStatus.FAILED
                passed = False
                message = f"Column validation failed: {len(missing_columns)} required column(s) missing"
            elif extra_columns and not self.allow_extra_columns:
                status = ValidationStatus.WARNING
                passed = False
                message = f"Column validation warning: {len(extra_columns)} unexpected column(s) found"
            else:
                status = ValidationStatus.PASSED
                passed = True
                message = f"All {len(required_cols)} required columns present"
                
                if present_optional:
                    message += f", {len(present_optional)} optional column(s) present"
                
                if extra_columns and self.allow_extra_columns:
                    message += f", {len(extra_columns)} extra column(s) allowed"
            
            execution_time = (time.time() - start_time) * 1000
            
            # Calculate metrics
            total_records = df.count() if passed else 0
            failed_records = 0 if passed else total_records
            
            return ValidationResult(
                validator_name=self.name,
                status=status,
                passed=passed,
                total_records=total_records,
                failed_records=failed_records,
                pass_rate=100.0 if passed else 0.0,
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
                total_records=0,
                failed_records=0,
                pass_rate=0.0,
                message=f"Column existence validation error: {str(e)}",
                details={},
                errors=[str(e)],
                execution_time_ms=execution_time
            )
