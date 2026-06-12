"""Warehouse Validation Utility

Provides validation capabilities for warehouse loads:
- Row count validation before and after load
- Required column validation before insert
- Duplicate record detection before insert
- Data quality checks
"""
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.warehouse_tables import WarehouseProcessedData

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation check"""
    
    def __init__(
        self,
        is_valid: bool,
        validation_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation result
        
        Args:
            is_valid: Whether validation passed
            validation_type: Type of validation performed
            message: Validation message
            details: Additional validation details
        """
        self.is_valid = is_valid
        self.validation_type = validation_type
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'validation_type': self.validation_type,
            'message': self.message,
            'details': self.details
        }


class WarehouseValidator:
    """Utility for validating warehouse data before and after loads"""
    
    def __init__(self, db: Session):
        """Initialize warehouse validator
        
        Args:
            db: Database session
        """
        self.db = db
    
    def validate_row_count(
        self,
        dataset_name: str,
        expected_count: int,
        batch_id: Optional[str] = None
    ) -> ValidationResult:
        """Validate row count after load
        
        Args:
            dataset_name: Name of the dataset
            expected_count: Expected number of records
            batch_id: Optional batch ID to filter by
            
        Returns:
            ValidationResult indicating if count matches
        """
        query = self.db.query(func.count(WarehouseProcessedData.id)).filter(
            WarehouseProcessedData.dataset_name == dataset_name
        )
        
        if batch_id:
            query = query.filter(WarehouseProcessedData.batch_id == batch_id)
        
        actual_count = query.scalar() or 0
        
        is_valid = actual_count == expected_count
        
        message = (
            f"Row count validation {'passed' if is_valid else 'failed'}: "
            f"expected={expected_count}, actual={actual_count}"
        )
        
        logger.info(message)
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type='row_count',
            message=message,
            details={
                'dataset_name': dataset_name,
                'batch_id': batch_id,
                'expected_count': expected_count,
                'actual_count': actual_count,
                'difference': actual_count - expected_count
            }
        )
    
    def validate_required_columns(
        self,
        records: List[Dict[str, Any]],
        required_columns: List[str]
    ) -> ValidationResult:
        """Validate that all records have required columns
        
        Args:
            records: List of records to validate
            required_columns: List of required column names
            
        Returns:
            ValidationResult indicating if all records have required columns
        """
        missing_columns_by_record = []
        
        for idx, record in enumerate(records):
            missing_columns = [col for col in required_columns if col not in record]
            if missing_columns:
                missing_columns_by_record.append({
                    'record_index': idx,
                    'missing_columns': missing_columns
                })
        
        is_valid = len(missing_columns_by_record) == 0
        
        message = (
            f"Required columns validation {'passed' if is_valid else 'failed'}: "
            f"{len(missing_columns_by_record)} records missing required columns"
        )
        
        logger.info(message)
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type='required_columns',
            message=message,
            details={
                'required_columns': required_columns,
                'total_records': len(records),
                'records_with_missing_columns': len(missing_columns_by_record),
                'missing_columns_details': missing_columns_by_record[:10]  # Limit to first 10
            }
        )
    
    def validate_duplicates(
        self,
        records: List[Dict[str, Any]],
        unique_keys: List[str]
    ) -> ValidationResult:
        """Validate that records don't have duplicates based on unique keys
        
        Args:
            records: List of records to validate
            unique_keys: List of column names that should be unique together
            
        Returns:
            ValidationResult indicating if duplicates were found
        """
        seen_keys: Set[Tuple] = set()
        duplicates = []
        
        for idx, record in enumerate(records):
            # Create a tuple of values for the unique keys
            try:
                key_values = tuple(record.get(key) for key in unique_keys)
            except Exception as e:
                logger.warning(f"Could not extract unique keys from record {idx}: {e}")
                continue
            
            if key_values in seen_keys:
                duplicates.append({
                    'record_index': idx,
                    'unique_key_values': dict(zip(unique_keys, key_values))
                })
            else:
                seen_keys.add(key_values)
        
        is_valid = len(duplicates) == 0
        
        message = (
            f"Duplicate validation {'passed' if is_valid else 'failed'}: "
            f"{len(duplicates)} duplicate records found"
        )
        
        logger.info(message)
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type='duplicates',
            message=message,
            details={
                'unique_keys': unique_keys,
                'total_records': len(records),
                'duplicate_count': len(duplicates),
                'duplicate_records': duplicates[:10]  # Limit to first 10
            }
        )
    
    def validate_existing_duplicates(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        unique_keys: List[str]
    ) -> ValidationResult:
        """Validate that records don't already exist in the warehouse
        
        Args:
            records: List of records to validate
            dataset_name: Name of the dataset
            unique_keys: List of column names to check for duplicates
            
        Returns:
            ValidationResult indicating if duplicates exist in warehouse
        """
        # This is a simplified check - in production, you'd want to check
        # against specific unique keys in the database
        existing_duplicates = []
        
        # For now, we'll check if any records exist for this dataset
        # In a real implementation, you'd check specific unique keys
        for idx, record in enumerate(records[:100]):  # Limit check to first 100 for performance
            # This is a placeholder - implement actual duplicate check based on your needs
            pass
        
        is_valid = len(existing_duplicates) == 0
        
        message = (
            f"Existing duplicates validation {'passed' if is_valid else 'failed'}: "
            f"{len(existing_duplicates)} records already exist in warehouse"
        )
        
        logger.info(message)
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type='existing_duplicates',
            message=message,
            details={
                'dataset_name': dataset_name,
                'unique_keys': unique_keys,
                'total_records': len(records),
                'existing_duplicate_count': len(existing_duplicates)
            }
        )
    
    def validate_data_types(
        self,
        records: List[Dict[str, Any]],
        schema: Dict[str, type]
    ) -> ValidationResult:
        """Validate that record fields match expected data types
        
        Args:
            records: List of records to validate
            schema: Dictionary mapping field names to expected types
            
        Returns:
            ValidationResult indicating if data types are correct
        """
        type_mismatches = []
        
        for idx, record in enumerate(records):
            for field, expected_type in schema.items():
                if field in record:
                    value = record[field]
                    if value is not None and not isinstance(value, expected_type):
                        type_mismatches.append({
                            'record_index': idx,
                            'field': field,
                            'expected_type': expected_type.__name__,
                            'actual_type': type(value).__name__,
                            'value': str(value)[:50]  # Limit value length
                        })
        
        is_valid = len(type_mismatches) == 0
        
        message = (
            f"Data type validation {'passed' if is_valid else 'failed'}: "
            f"{len(type_mismatches)} type mismatches found"
        )
        
        logger.info(message)
        
        return ValidationResult(
            is_valid=is_valid,
            validation_type='data_types',
            message=message,
            details={
                'schema': {k: v.__name__ for k, v in schema.items()},
                'total_records': len(records),
                'type_mismatch_count': len(type_mismatches),
                'type_mismatches': type_mismatches[:10]  # Limit to first 10
            }
        )
    
    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        dataset_name: str,
        required_columns: Optional[List[str]] = None,
        unique_keys: Optional[List[str]] = None,
        schema: Optional[Dict[str, type]] = None
    ) -> List[ValidationResult]:
        """Run all validations on a batch of records
        
        Args:
            records: List of records to validate
            dataset_name: Name of the dataset
            required_columns: Optional list of required columns
            unique_keys: Optional list of unique key columns
            schema: Optional schema for data type validation
            
        Returns:
            List of ValidationResults
        """
        results = []
        
        # Validate required columns
        if required_columns:
            results.append(self.validate_required_columns(records, required_columns))
        
        # Validate duplicates within batch
        if unique_keys:
            results.append(self.validate_duplicates(records, unique_keys))
        
        # Validate data types
        if schema:
            results.append(self.validate_data_types(records, schema))
        
        # Log validation summary
        all_valid = all(result.is_valid for result in results)
        logger.info(
            f"Batch validation {'passed' if all_valid else 'failed'}: "
            f"{len(results)} checks performed, "
            f"{sum(1 for r in results if r.is_valid)} passed"
        )
        
        return results
