"""Validation aggregator service for combining multiple validator results."""

from typing import List, Optional
from datetime import datetime
from pyspark.sql import DataFrame

from app.validators import (
    BaseValidator,
    ValidationResult,
    ValidationStatus,
    SchemaValidator,
    NullValidator,
    ChecksumValidator,
    DatatypeValidator,
    ColumnExistenceValidator,
)
from app.schemas.validation_schema import ValidationSummary, ValidatorSummary


class ValidationAggregator:
    """
    Aggregates results from multiple validators into a unified summary.
    
    Executes schema, null, datatype, checksum, and column existence validators
    and provides a comprehensive validation report.
    """
    
    def __init__(self):
        """Initialize the validation aggregator."""
        self.validators: List[BaseValidator] = []
        self.results: List[ValidationResult] = []
    
    def add_validator(self, validator: BaseValidator) -> None:
        """
        Add a validator to the aggregation pipeline.
        
        Args:
            validator: Validator instance to add
        """
        self.validators.append(validator)
    
    def clear_validators(self) -> None:
        """Remove all validators from the pipeline."""
        self.validators.clear()
        self.results.clear()
    
    def validate(
        self,
        df: DataFrame,
        dataset_name: str,
        **kwargs
    ) -> ValidationSummary:
        """
        Execute all validators and aggregate results.
        
        Args:
            df: DataFrame to validate
            dataset_name: Name of the dataset being validated
            **kwargs: Additional parameters passed to validators
            
        Returns:
            ValidationSummary with aggregated results
        """
        self.results.clear()
        validation_timestamp = datetime.utcnow()
        
        # Execute all validators
        for validator in self.validators:
            try:
                result = validator.validate(df, **kwargs)
                self.results.append(result)
            except Exception as e:
                # Create error result for failed validator
                error_result = ValidationResult(
                    validator_name=validator.name,
                    status=ValidationStatus.ERROR,
                    passed=False,
                    total_records=0,
                    failed_records=0,
                    pass_rate=0.0,
                    message=f"Validator execution failed: {str(e)}",
                    errors=[str(e)]
                )
                self.results.append(error_result)
        
        # Aggregate results
        return self._aggregate_results(dataset_name, validation_timestamp)
    
    def validate_with_defaults(
        self,
        df: DataFrame,
        dataset_name: str,
        schema_contract: Optional[dict] = None,
        **kwargs
    ) -> ValidationSummary:
        """
        Execute validation with default validator set.
        
        Creates and executes a standard set of validators:
        - Column existence validator
        - Schema validator
        - Null validator
        - Datatype validator
        - Checksum validator
        
        Args:
            df: DataFrame to validate
            dataset_name: Name of the dataset
            schema_contract: Optional schema contract dict
            **kwargs: Additional parameters
            
        Returns:
            ValidationSummary with aggregated results
        """
        self.clear_validators()
        
        # Add column existence validator
        if schema_contract and 'columns' in schema_contract:
            required_cols = [
                col['name'] for col in schema_contract['columns']
                if col.get('required', True)
            ]
            optional_cols = [
                col['name'] for col in schema_contract['columns']
                if not col.get('required', True)
            ]
            self.add_validator(
                ColumnExistenceValidator(
                    required_columns=required_cols,
                    optional_columns=optional_cols
                )
            )
        
        # Add schema validator
        if schema_contract:
            column_types = {}
            if 'columns' in schema_contract:
                column_types = {
                    col['name']: col['type']
                    for col in schema_contract['columns']
                }
            self.add_validator(SchemaValidator(column_types=column_types))
        
        # Add null validator
        null_threshold = kwargs.get('null_threshold', 5.0)
        self.add_validator(NullValidator(max_null_percentage=null_threshold))
        
        # Add datatype validator
        if schema_contract and 'columns' in schema_contract:
            column_types = {
                col['name']: col['type']
                for col in schema_contract['columns']
            }
            self.add_validator(DatatypeValidator(column_types=column_types))
        
        # Add checksum validator
        checksum_column = kwargs.get('checksum_column')
        expected_checksum = kwargs.get('expected_checksum')
        if checksum_column or expected_checksum:
            self.add_validator(
                ChecksumValidator(
                    checksum_column=checksum_column,
                    expected_checksum=expected_checksum
                )
            )
        
        return self.validate(df, dataset_name, **kwargs)
    
    def _aggregate_results(
        self,
        dataset_name: str,
        validation_timestamp: datetime
    ) -> ValidationSummary:
        """
        Aggregate individual validation results into a summary.
        
        Args:
            dataset_name: Name of the dataset
            validation_timestamp: When validation was performed
            
        Returns:
            ValidationSummary with aggregated metrics
        """
        # Count validators by status
        passed_count = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed_count = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warning_count = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        error_count = sum(1 for r in self.results if r.status == ValidationStatus.ERROR)
        
        # Determine overall status
        if error_count > 0:
            overall_status = ValidationStatus.ERROR
            overall_passed = False
        elif failed_count > 0:
            overall_status = ValidationStatus.FAILED
            overall_passed = False
        elif warning_count > 0:
            overall_status = ValidationStatus.WARNING
            overall_passed = False
        else:
            overall_status = ValidationStatus.PASSED
            overall_passed = True
        
        # Calculate total execution time
        total_execution_time = sum(
            r.execution_time_ms for r in self.results
            if r.execution_time_ms is not None
        )
        
        # Get total records (from first result that has it)
        total_records = 0
        for result in self.results:
            if result.total_records > 0:
                total_records = result.total_records
                break
        
        # Convert results to validator summaries
        validator_summaries = [
            ValidatorSummary(
                validator_name=r.validator_name,
                status=r.status,
                passed=r.passed,
                total_records=r.total_records,
                failed_records=r.failed_records,
                pass_rate=r.pass_rate,
                message=r.message,
                execution_time_ms=r.execution_time_ms,
                errors=r.errors
            )
            for r in self.results
        ]
        
        # Create validation summary
        return ValidationSummary(
            dataset_name=dataset_name,
            validation_timestamp=validation_timestamp,
            overall_status=overall_status,
            overall_passed=overall_passed,
            total_validators=len(self.results),
            passed_validators=passed_count,
            failed_validators=failed_count,
            warning_validators=warning_count,
            error_validators=error_count,
            total_records=total_records,
            total_execution_time_ms=total_execution_time,
            validators=validator_summaries,
            metadata={
                'dataset_name': dataset_name,
                'validators_executed': [r.validator_name for r in self.results]
            }
        )
    
    def get_last_summary(self) -> Optional[ValidationSummary]:
        """
        Get the summary from the last validation run.
        
        Returns:
            Last ValidationSummary or None if no validations run
        """
        if not self.results:
            return None
        
        # Reconstruct summary from cached results
        return self._aggregate_results("last_validation", datetime.utcnow())
