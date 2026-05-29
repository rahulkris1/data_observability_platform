"""Schema Contract Service

Provides functionality for loading, managing, and validating schema contracts
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.schemas.contract_schema import (
    SchemaContractCreate,
    SchemaContractResponse,
    ContractValidationResult,
    ContractValidationSummary,
    ValidationError,
    ValidateDatasetRequest,
    DataType,
    ColumnDefinition,
)


class SchemaContractService:
    """Service for managing and validating schema contracts"""
    
    def __init__(self, contracts_dir: Optional[str] = None):
        """Initialize the schema contract service
        
        Args:
            contracts_dir: Directory containing contract JSON files.
                          Defaults to backend/contracts/
        """
        if contracts_dir is None:
            # Default to backend/contracts directory
            backend_dir = Path(__file__).parent.parent.parent
            self.contracts_dir = backend_dir / "contracts"
        else:
            self.contracts_dir = Path(contracts_dir)
        
        # In-memory storage for contracts (no database persistence yet)
        self._contracts: Dict[str, SchemaContractResponse] = {}
        self._validation_results: List[ContractValidationResult] = []
        
        # Load contracts from directory on initialization
        self.load_contracts_from_directory()
    
    def load_contracts_from_directory(self) -> None:
        """Load all contract JSON files from the contracts directory"""
        if not self.contracts_dir.exists():
            return
        
        for json_file in self.contracts_dir.glob("*.json"):
            try:
                self.load_contract_from_file(json_file)
            except Exception as e:
                print(f"Error loading contract from {json_file}: {e}")
    
    def load_contract_from_file(self, file_path: Path) -> SchemaContractResponse:
        """Load a single contract from a JSON file
        
        Args:
            file_path: Path to the contract JSON file
            
        Returns:
            SchemaContractResponse object
        """
        with open(file_path, 'r') as f:
            contract_data = json.load(f)
        
        # Create a contract response object with dummy ID and timestamps
        contract = SchemaContractResponse(
            id=len(self._contracts) + 1,
            name=contract_data["name"],
            description=contract_data.get("description"),
            dataset_name=contract_data["dataset_name"],
            version=contract_data.get("version", "1.0.0"),
            is_active=contract_data.get("is_active", True),
            schema_definition=contract_data["schema_definition"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Store in memory
        self._contracts[contract.name] = contract
        
        return contract
    
    def get_contract_by_name(self, name: str) -> Optional[SchemaContractResponse]:
        """Get a contract by name
        
        Args:
            name: Contract name
            
        Returns:
            SchemaContractResponse if found, None otherwise
        """
        return self._contracts.get(name)
    
    def get_all_contracts(self) -> List[SchemaContractResponse]:
        """Get all loaded contracts
        
        Returns:
            List of all schema contracts
        """
        return list(self._contracts.values())
    
    def validate_dataset(
        self, 
        contract_name: str, 
        dataset_columns: List[Dict[str, str]]
    ) -> ContractValidationResult:
        """Validate a dataset against a schema contract
        
        Args:
            contract_name: Name of the contract to validate against
            dataset_columns: List of dataset columns with name and data_type
                            Example: [{"name": "customer_id", "data_type": "integer"}, ...]
        
        Returns:
            ContractValidationResult with validation results
        """
        # Get the contract
        contract = self.get_contract_by_name(contract_name)
        if not contract:
            raise ValueError(f"Contract '{contract_name}' not found")
        
        # Extract expected columns from contract
        expected_columns = contract.schema_definition["columns"]
        
        # Create maps for easier lookup
        expected_columns_map = {col["name"]: col for col in expected_columns}
        actual_columns_map = {col["name"]: col for col in dataset_columns}
        
        # Collect validation errors
        errors: List[ValidationError] = []
        
        # Check for missing required columns
        for expected_col in expected_columns:
            col_name = expected_col["name"]
            if expected_col.get("required", True) and col_name not in actual_columns_map:
                errors.append(ValidationError(
                    error_type="missing_column",
                    column_name=col_name,
                    expected=f"Required column: {col_name}",
                    actual="Column not found",
                    message=f"Required column '{col_name}' is missing from dataset"
                ))
        
        # Check for extra columns not in contract
        for actual_col_name in actual_columns_map.keys():
            if actual_col_name not in expected_columns_map:
                errors.append(ValidationError(
                    error_type="unexpected_column",
                    column_name=actual_col_name,
                    expected="Column should not exist",
                    actual=f"Column found: {actual_col_name}",
                    message=f"Column '{actual_col_name}' exists in dataset but not in contract"
                ))
        
        # Check data types for matching columns
        for col_name, expected_col in expected_columns_map.items():
            if col_name in actual_columns_map:
                actual_col = actual_columns_map[col_name]
                expected_type = expected_col["data_type"]
                actual_type = actual_col.get("data_type", "unknown")
                
                # Normalize type names for comparison
                expected_type_normalized = self._normalize_data_type(expected_type)
                actual_type_normalized = self._normalize_data_type(actual_type)
                
                if expected_type_normalized != actual_type_normalized:
                    errors.append(ValidationError(
                        error_type="type_mismatch",
                        column_name=col_name,
                        expected=expected_type,
                        actual=actual_type,
                        message=f"Column '{col_name}' has type '{actual_type}' but expected '{expected_type}'"
                    ))
        
        # Create validation result
        result = ContractValidationResult(
            is_valid=len(errors) == 0,
            contract_name=contract_name,
            dataset_name=contract.dataset_name,
            errors=errors,
            validated_at=datetime.utcnow(),
            total_columns_expected=len(expected_columns),
            total_columns_actual=len(dataset_columns),
        )
        
        # Store result in memory
        self._validation_results.append(result)
        
        return result
    
    def _normalize_data_type(self, data_type: str) -> str:
        """Normalize data type names for comparison
        
        Args:
            data_type: Data type string
            
        Returns:
            Normalized data type
        """
        type_mapping = {
            "int": "integer",
            "int64": "integer",
            "int32": "integer",
            "long": "integer",
            "str": "string",
            "object": "string",
            "varchar": "string",
            "text": "string",
            "char": "string",
            "float64": "float",
            "float32": "float",
            "double": "float",
            "decimal": "float",
            "bool": "boolean",
            "datetime": "timestamp",
            "datetime64": "timestamp",
            "time": "timestamp",
        }
        
        normalized = data_type.lower().strip()
        return type_mapping.get(normalized, normalized)
    
    def get_validation_results(
        self, 
        dataset_name: Optional[str] = None,
        is_valid: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContractValidationResult]:
        """Get validation results with optional filtering
        
        Args:
            dataset_name: Filter by dataset name
            is_valid: Filter by validation status
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of validation results
        """
        results = self._validation_results
        
        # Apply filters
        if dataset_name:
            results = [r for r in results if r.dataset_name == dataset_name]
        
        if is_valid is not None:
            results = [r for r in results if r.is_valid == is_valid]
        
        # Sort by validated_at descending (most recent first)
        results = sorted(results, key=lambda r: r.validated_at, reverse=True)
        
        # Apply pagination
        return results[offset:offset + limit]
    
    def get_validation_summary(self) -> ContractValidationSummary:
        """Get summary statistics of all validations
        
        Returns:
            ContractValidationSummary with aggregated statistics
        """
        total = len(self._validation_results)
        passed = sum(1 for r in self._validation_results if r.is_valid)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0.0
        
        return ContractValidationSummary(
            total_validations=total,
            passed=passed,
            failed=failed,
            success_rate=round(success_rate, 2),
        )
    
    def create_contract(self, contract_data: SchemaContractCreate) -> SchemaContractResponse:
        """Create a new schema contract
        
        Args:
            contract_data: Contract creation data
            
        Returns:
            Created schema contract
        """
        # Check if contract already exists
        if contract_data.name in self._contracts:
            raise ValueError(f"Contract '{contract_data.name}' already exists")
        
        # Create contract response
        contract = SchemaContractResponse(
            id=len(self._contracts) + 1,
            name=contract_data.name,
            description=contract_data.description,
            dataset_name=contract_data.dataset_name,
            version=contract_data.version,
            is_active=contract_data.is_active,
            schema_definition=contract_data.schema_definition.dict(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Store in memory
        self._contracts[contract.name] = contract
        
        return contract


# Global service instance
_service_instance: Optional[SchemaContractService] = None


def get_schema_contract_service() -> SchemaContractService:
    """Get or create the global schema contract service instance
    
    Returns:
        SchemaContractService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = SchemaContractService()
    return _service_instance
