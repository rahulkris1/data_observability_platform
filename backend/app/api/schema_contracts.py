"""Schema Contract API Router

Endpoints for managing and validating schema contracts
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import logging

from app.schemas.contract_schema import (
    SchemaContractResponse,
    ContractValidationResult,
    ContractValidationSummary,
    ValidateDatasetRequest,
    SchemaContractCreate,
)
from app.services.schema_contract_service import get_schema_contract_service
from app.services.cache_service import get_cache_service
from app.services.cache_invalidation_service import get_cache_invalidation_service

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/schema-contracts", tags=["Schema Contracts"])


@router.get("/", response_model=List[SchemaContractResponse])
async def list_contracts():
    """Get all available schema contracts"""
    cache_service = get_cache_service()
    
    # Try to get from cache
    cached = cache_service.get("all_contracts", prefix="schema_contracts:list:")
    if cached:
        logger.info("Returning cached contract list")
        return cached
    
    # If not cached, fetch from service
    service = get_schema_contract_service()
    contracts = service.get_all_contracts()
    
    # Cache the result for 30 minutes
    cache_service.set("all_contracts", contracts, prefix="schema_contracts:list:", ttl=1800)
    
    return contracts


@router.get("/{contract_name}", response_model=SchemaContractResponse)
async def get_contract(contract_name: str):
    """Get a specific schema contract by name"""
    cache_service = get_cache_service()
    
    # Try to get from cache
    cached = cache_service.get_schema_contract(contract_name)
    if cached:
        logger.info(f"Returning cached contract for {contract_name}")
        return cached
    
    # If not cached, fetch from service
    service = get_schema_contract_service()
    contract = service.get_contract_by_name(contract_name)
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract '{contract_name}' not found"
        )
    
    # Cache the contract
    cache_service.set_schema_contract(contract_name, contract)
    
    return contract


@router.post("/", response_model=SchemaContractResponse, status_code=201)
async def create_contract(contract_data: SchemaContractCreate):
    """Create a new schema contract"""
    service = get_schema_contract_service()
    cache_service = get_cache_service()
    invalidation_service = get_cache_invalidation_service()
    
    try:
        contract = service.create_contract(contract_data)
        
        # Invalidate related caches
        invalidation_service.invalidate_on_contract_update(
            table_name=contract_data.table_name,
            updated_by="api",
            reason="Contract created"
        )
        
        # Invalidate list cache
        cache_service.delete("all_contracts", prefix="schema_contracts:list:")
        
        # Cache the new contract
        cache_service.set_schema_contract(contract_data.table_name, contract)
        
        return contract
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=ContractValidationResult)
async def validate_dataset(request: ValidateDatasetRequest):
    """Validate a dataset against a schema contract"""
    service = get_schema_contract_service()
    
    try:
        result = service.validate_dataset(
            contract_name=request.contract_name,
            dataset_columns=request.dataset_columns,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validations/results", response_model=List[ContractValidationResult])
async def get_validation_results(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    is_valid: Optional[bool] = Query(None, description="Filter by validation status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """Get validation results with optional filtering and pagination"""
    service = get_schema_contract_service()
    
    results = service.get_validation_results(
        dataset_name=dataset_name,
        is_valid=is_valid,
        limit=limit,
        offset=offset,
    )
    
    return results


@router.get("/validations/summary", response_model=ContractValidationSummary)
async def get_validation_summary():
    """Get summary statistics of all validations"""
    service = get_schema_contract_service()
    return service.get_validation_summary()
