"""Pydantic Schemas Package

This package contains Pydantic models for request/response validation.
Schemas define the API contract and data validation rules.
"""
from app.schemas.contract_schema import (
    DataType,
    ColumnDefinition,
    SchemaDefinition,
    SchemaContractCreate,
    SchemaContractResponse,
    ValidationError,
    ContractValidationResult,
    ContractValidationSummary,
    ValidateDatasetRequest,
)
from app.schemas.validation_schema import (
    ValidatorSummary,
    ValidationSummary,
    ValidationHistoryItem,
    ValidationMetrics,
)
from app.schemas.integrity_schema import (
    FailedRowRecord,
    FailedRowsResponse,
    DuplicateKeyInfo,
    OrphanForeignKeyInfo,
    PrimaryKeyValidationResult,
    ForeignKeyValidationResult,
    IntegrityValidationSummary,
    IntegrityViolation,
    IntegrityViolationsResponse,
)
from app.schemas.dag_execution_schema import (
    DAGExecutionResponse,
    DAGExecutionListResponse,
    DAGExecutionSummary,
)

__all__ = [
    "DataType",
    "ColumnDefinition",
    "SchemaDefinition",
    "SchemaContractCreate",
    "SchemaContractResponse",
    "ValidationError",
    "ContractValidationResult",
    "ContractValidationSummary",
    "ValidateDatasetRequest",
    "ValidatorSummary",
    "ValidationSummary",
    "ValidationHistoryItem",
    "ValidationMetrics",
    "FailedRowRecord",
    "FailedRowsResponse",
    "DuplicateKeyInfo",
    "OrphanForeignKeyInfo",
    "PrimaryKeyValidationResult",
    "ForeignKeyValidationResult",
    "IntegrityValidationSummary",
    "IntegrityViolation",
    "IntegrityViolationsResponse",
    "DAGExecutionResponse",
    "DAGExecutionListResponse",
    "DAGExecutionSummary",
]
