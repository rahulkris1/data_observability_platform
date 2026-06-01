"""Validation Log Service

Provides functionality for storing and retrieving validation execution logs
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.validation_log import ValidationLog
from app.schemas.validation_schema import (
    ValidationSummary,
    ValidationHistoryItem,
    ValidationMetrics,
)
from app.validators.base_validator import ValidationResult


class ValidationLogService:
    """Service for managing validation execution logs in PostgreSQL"""
    
    def __init__(self, db: Session):
        """
        Initialize the validation log service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def log_validation_result(
        self,
        result: ValidationResult,
        dataset_name: str,
        validation_type: str
    ) -> ValidationLog:
        """
        Store a single validation result in the database.
        
        Args:
            result: ValidationResult to store
            dataset_name: Name of the dataset
            validation_type: Type of validation (e.g., 'schema', 'null', 'datatype')
            
        Returns:
            Created ValidationLog instance
        """
        log_entry = ValidationLog(
            dataset_name=dataset_name,
            validation_type=validation_type,
            status=result.status.value,
            total_records=result.total_records,
            failed_records=result.failed_records,
            pass_rate=result.pass_rate,
            execution_time_ms=result.execution_time_ms,
            validator_name=result.validator_name,
            message=result.message,
            details=result.details,
            errors=result.errors
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        return log_entry
    
    def log_validation_summary(
        self,
        summary: ValidationSummary
    ) -> List[ValidationLog]:
        """
        Store aggregated validation summary in the database.
        
        Creates individual log entries for each validator and one for the overall summary.
        
        Args:
            summary: ValidationSummary to store
            
        Returns:
            List of created ValidationLog instances
        """
        log_entries = []
        
        # Log each individual validator result
        for validator_summary in summary.validators:
            log_entry = ValidationLog(
                dataset_name=summary.dataset_name,
                validation_type=validator_summary.validator_name.lower().replace('validator', '').strip(),
                status=validator_summary.status.value,
                total_records=validator_summary.total_records,
                failed_records=validator_summary.failed_records,
                pass_rate=validator_summary.pass_rate,
                execution_time_ms=validator_summary.execution_time_ms,
                validator_name=validator_summary.validator_name,
                message=validator_summary.message,
                details={},
                errors=validator_summary.errors
            )
            self.db.add(log_entry)
            log_entries.append(log_entry)
        
        # Log overall aggregated result
        overall_log = ValidationLog(
            dataset_name=summary.dataset_name,
            validation_type='aggregated',
            status=summary.overall_status.value,
            total_records=summary.total_records,
            failed_records=0,
            pass_rate=100.0 if summary.overall_passed else 0.0,
            execution_time_ms=summary.total_execution_time_ms,
            validator_name='ValidationAggregator',
            message=f"Executed {summary.total_validators} validators: "
                   f"{summary.passed_validators} passed, "
                   f"{summary.failed_validators} failed, "
                   f"{summary.warning_validators} warnings",
            details={
                'total_validators': summary.total_validators,
                'passed_validators': summary.passed_validators,
                'failed_validators': summary.failed_validators,
                'warning_validators': summary.warning_validators,
                'error_validators': summary.error_validators,
            },
            errors=[]
        )
        self.db.add(overall_log)
        log_entries.append(overall_log)
        
        self.db.commit()
        
        # Refresh all entries
        for entry in log_entries:
            self.db.refresh(entry)
        
        return log_entries
    
    def get_validation_history(
        self,
        dataset_name: Optional[str] = None,
        validation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ValidationHistoryItem]:
        """
        Retrieve validation history with optional filters.
        
        Args:
            dataset_name: Filter by dataset name
            validation_type: Filter by validation type
            status: Filter by status
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of ValidationHistoryItem objects
        """
        query = self.db.query(ValidationLog)
        
        # Apply filters
        if dataset_name:
            query = query.filter(ValidationLog.dataset_name == dataset_name)
        if validation_type:
            query = query.filter(ValidationLog.validation_type == validation_type)
        if status:
            query = query.filter(ValidationLog.status == status)
        
        # Order by most recent first
        query = query.order_by(desc(ValidationLog.created_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query and convert to schema
        logs = query.all()
        
        return [
            ValidationHistoryItem(
                id=log.id,
                dataset_name=log.dataset_name,
                validation_type=log.validation_type,
                status=log.status,
                executed_at=log.created_at,
                execution_time_ms=log.execution_time_ms,
                total_records=log.total_records,
                failed_records=log.failed_records,
                pass_rate=log.pass_rate
            )
            for log in logs
        ]
    
    def get_validation_metrics(
        self,
        dataset_name: Optional[str] = None,
        days: int = 30
    ) -> ValidationMetrics:
        """
        Calculate validation metrics for dashboard.
        
        Args:
            dataset_name: Optional filter by dataset name
            days: Number of days to look back (default: 30)
            
        Returns:
            ValidationMetrics with aggregated statistics
        """
        # Calculate cutoff date
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        
        query = self.db.query(ValidationLog).filter(
            ValidationLog.created_at >= cutoff_date
        )
        
        if dataset_name:
            query = query.filter(ValidationLog.dataset_name == dataset_name)
        
        # Get all validation logs
        logs = query.all()
        
        if not logs:
            return ValidationMetrics(
                total_validations=0,
                passed_validations=0,
                failed_validations=0,
                warning_validations=0,
                average_pass_rate=0.0
            )
        
        # Calculate metrics
        total_validations = len(logs)
        passed_validations = sum(1 for log in logs if log.status == 'passed')
        failed_validations = sum(1 for log in logs if log.status == 'failed')
        warning_validations = sum(1 for log in logs if log.status == 'warning')
        
        # Calculate average pass rate
        total_pass_rate = sum(log.pass_rate for log in logs)
        average_pass_rate = total_pass_rate / total_validations if total_validations > 0 else 0.0
        
        return ValidationMetrics(
            total_validations=total_validations,
            passed_validations=passed_validations,
            failed_validations=failed_validations,
            warning_validations=warning_validations,
            average_pass_rate=round(average_pass_rate, 2)
        )
    
    def get_validation_by_id(self, log_id: int) -> Optional[ValidationLog]:
        """
        Get a specific validation log by ID.
        
        Args:
            log_id: ID of the validation log
            
        Returns:
            ValidationLog instance or None if not found
        """
        return self.db.query(ValidationLog).filter(ValidationLog.id == log_id).first()
    
    def delete_old_logs(self, days: int = 90) -> int:
        """
        Delete validation logs older than specified days.
        
        Args:
            days: Delete logs older than this many days
            
        Returns:
            Number of deleted records
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = self.db.query(ValidationLog).filter(
            ValidationLog.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted_count
    
    def get_dataset_statistics(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with dataset statistics
        """
        # Get most recent validation log for the dataset
        latest_log = self.db.query(ValidationLog).filter(
            ValidationLog.dataset_name == dataset_name
        ).order_by(desc(ValidationLog.created_at)).first()
        
        if not latest_log:
            return {
                'dataset_name': dataset_name,
                'row_count': 0,
                'column_count': 0,
                'validation_score': 0.0,
                'last_validated': None
            }
        
        # Extract details
        row_count = latest_log.total_records
        column_count = 0
        if latest_log.details and 'columns_checked' in latest_log.details:
            column_count = latest_log.details['columns_checked']
        
        # Calculate validation score (average pass rate for this dataset)
        avg_pass_rate = self.db.query(func.avg(ValidationLog.pass_rate)).filter(
            ValidationLog.dataset_name == dataset_name
        ).scalar() or 0.0
        
        return {
            'dataset_name': dataset_name,
            'row_count': row_count,
            'column_count': column_count,
            'validation_score': round(avg_pass_rate, 2),
            'last_validated': latest_log.created_at
        }
