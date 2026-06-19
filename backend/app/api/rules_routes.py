"""Rules Management API routes.

API endpoints for managing validation rules configuration.
"""

import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.rule_schema import (
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleResponse,
    RuleListResponse,
    RuleToggleRequest,
    RuleToggleResponse,
    RuleExecutionRequest,
    RuleExecutionResponse,
    RuleExecutionResult,
    ThresholdEvaluationResult,
)
from app.validators.validation_rules_engine import ValidationRulesEngine
from app.validators.rules_parser import RuleDefinition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/rules",
    tags=["rules"]
)

# Default rules configuration path
DEFAULT_RULES_CONFIG = "backend/config/validation_rules.json"

# Global rules engine instance
_rules_engine: Optional[ValidationRulesEngine] = None


def get_rules_engine() -> ValidationRulesEngine:
    """Get or initialize the global rules engine."""
    global _rules_engine
    
    if _rules_engine is None:
        config_path = Path(DEFAULT_RULES_CONFIG)
        
        if config_path.exists():
            try:
                _rules_engine = ValidationRulesEngine(str(config_path))
                logger.info(f"Loaded rules configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load rules configuration: {e}")
                # Initialize with empty config
                _rules_engine = ValidationRulesEngine()
                _rules_engine.load_rules_from_dict({"version": "1.0", "rules": []})
        else:
            logger.warning(f"Rules configuration not found at {config_path}, initializing empty")
            _rules_engine = ValidationRulesEngine()
            _rules_engine.load_rules_from_dict({"version": "1.0", "rules": []})
    
    return _rules_engine


def rule_to_response(rule: RuleDefinition) -> RuleResponse:
    """Convert RuleDefinition to RuleResponse."""
    return RuleResponse(
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type.value,
        enabled=rule.enabled,
        target_columns=rule.target_columns,
        parameters=rule.parameters,
        thresholds=[
            {
                "metric": t.metric,
                "operator": t.operator.value,
                "value": t.value
            }
            for t in rule.thresholds
        ],
        severity=rule.severity,
        tags=rule.tags
    )


@router.get(
    "",
    response_model=RuleListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all rules",
    description="Retrieve all validation rules from configuration"
)
async def get_all_rules(
    enabled_only: bool = False
) -> RuleListResponse:
    """Get all validation rules."""
    try:
        engine = get_rules_engine()
        
        if not engine.rules_config:
            return RuleListResponse(
                version="1.0",
                total_rules=0,
                enabled_rules=0,
                disabled_rules=0,
                rules=[]
            )
        
        rules = engine.get_enabled_rules() if enabled_only else engine.rules_config.rules
        enabled_count = len([r for r in engine.rules_config.rules if r.enabled])
        
        return RuleListResponse(
            version=engine.rules_config.version,
            total_rules=len(engine.rules_config.rules),
            enabled_rules=enabled_count,
            disabled_rules=len(engine.rules_config.rules) - enabled_count,
            rules=[rule_to_response(rule) for rule in rules]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rules: {str(e)}"
        )


@router.get(
    "/{rule_id}",
    response_model=RuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific rule",
    description="Retrieve a specific validation rule by ID"
)
async def get_rule(rule_id: str) -> RuleResponse:
    """Get a specific rule by ID."""
    try:
        engine = get_rules_engine()
        rule = engine.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID '{rule_id}' not found"
            )
        
        return rule_to_response(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rule: {str(e)}"
        )


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new rule",
    description="Create a new validation rule in configuration"
)
async def create_rule(rule_request: RuleCreateRequest) -> RuleResponse:
    """Create a new validation rule."""
    try:
        engine = get_rules_engine()
        
        # Check if rule already exists
        existing_rule = engine.get_rule(rule_request.rule_id)
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule with ID '{rule_request.rule_id}' already exists"
            )
        
        # Create new rule
        new_rule = RuleDefinition(**rule_request.dict())
        
        # Add to configuration
        if not engine.rules_config:
            engine.load_rules_from_dict({"version": "1.0", "rules": []})
        
        engine.rules_config.rules.append(new_rule)
        
        # Save configuration
        if engine.config_path:
            engine.save_rules()
        
        logger.info(f"Created new rule: {rule_request.rule_id}")
        return rule_to_response(new_rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}"
        )


@router.put(
    "/{rule_id}",
    response_model=RuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update rule",
    description="Update an existing validation rule"
)
async def update_rule(
    rule_id: str,
    rule_request: RuleUpdateRequest
) -> RuleResponse:
    """Update an existing validation rule."""
    try:
        engine = get_rules_engine()
        rule = engine.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID '{rule_id}' not found"
            )
        
        # Update fields
        update_data = rule_request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
        
        # Save configuration
        if engine.config_path:
            engine.save_rules()
        
        logger.info(f"Updated rule: {rule_id}")
        return rule_to_response(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}"
        )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete rule",
    description="Delete a validation rule from configuration"
)
async def delete_rule(rule_id: str) -> JSONResponse:
    """Delete a validation rule."""
    try:
        engine = get_rules_engine()
        
        if not engine.rules_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID '{rule_id}' not found"
            )
        
        # Find and remove rule
        rule_found = False
        for i, rule in enumerate(engine.rules_config.rules):
            if rule.rule_id == rule_id:
                engine.rules_config.rules.pop(i)
                rule_found = True
                break
        
        if not rule_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID '{rule_id}' not found"
            )
        
        # Save configuration
        if engine.config_path:
            engine.save_rules()
        
        logger.info(f"Deleted rule: {rule_id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Rule '{rule_id}' deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}"
        )


@router.patch(
    "/{rule_id}/toggle",
    response_model=RuleToggleResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle rule enable/disable",
    description="Enable or disable a validation rule"
)
async def toggle_rule(
    rule_id: str,
    toggle_request: RuleToggleRequest
) -> RuleToggleResponse:
    """Enable or disable a validation rule."""
    try:
        engine = get_rules_engine()
        
        if toggle_request.enabled:
            success = engine.enable_rule(rule_id)
            action = "enabled"
        else:
            success = engine.disable_rule(rule_id)
            action = "disabled"
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID '{rule_id}' not found"
            )
        
        # Save configuration
        if engine.config_path:
            engine.save_rules()
        
        logger.info(f"{action.capitalize()} rule: {rule_id}")
        return RuleToggleResponse(
            rule_id=rule_id,
            enabled=toggle_request.enabled,
            message=f"Rule '{rule_id}' {action} successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle rule: {str(e)}"
        )


@router.get(
    "/types/list",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get available rule types",
    description="List all available validation rule types"
)
async def get_rule_types() -> List[str]:
    """Get list of available rule types."""
    from app.validators.rules_parser import RuleType
    return [rt.value for rt in RuleType]


@router.get(
    "/tags/list",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get all tags",
    description="Get all unique tags used across rules"
)
async def get_all_tags() -> List[str]:
    """Get all unique tags."""
    try:
        engine = get_rules_engine()
        
        if not engine.rules_config:
            return []
        
        tags = set()
        for rule in engine.rules_config.rules:
            tags.update(rule.tags)
        
        return sorted(list(tags))
        
    except Exception as e:
        logger.error(f"Error retrieving tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tags: {str(e)}"
        )
