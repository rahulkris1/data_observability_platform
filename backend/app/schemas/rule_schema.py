"""Rule schemas for API requests and responses.

Schemas for validation rule management via REST API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.validators.rules_parser import RuleType, ThresholdOperator


class ThresholdSchema(BaseModel):
    """Schema for validation threshold."""
    
    metric: str = Field(..., description="Metric name (e.g., 'pass_rate', 'failed_records')")
    operator: ThresholdOperator = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")
    
    class Config:
        use_enum_values = True


class RuleCreateRequest(BaseModel):
    """Request schema for creating a new rule."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    rule_type: RuleType = Field(..., description="Type of validation rule")
    enabled: bool = Field(True, description="Whether rule is active")
    
    target_columns: List[str] = Field(default_factory=list, description="Columns to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific parameters")
    
    thresholds: List[ThresholdSchema] = Field(
        default_factory=list, 
        description="Validation thresholds"
    )
    
    severity: str = Field("error", description="Rule severity: error, warning, info")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    
    @validator('rule_id')
    def validate_rule_id(cls, v):
        """Ensure rule_id is not empty."""
        if not v or not v.strip():
            raise ValueError("rule_id cannot be empty")
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()
    
    class Config:
        use_enum_values = True


class RuleUpdateRequest(BaseModel):
    """Request schema for updating an existing rule."""
    
    name: Optional[str] = Field(None, description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    rule_type: Optional[RuleType] = Field(None, description="Type of validation rule")
    enabled: Optional[bool] = Field(None, description="Whether rule is active")
    
    target_columns: Optional[List[str]] = Field(None, description="Columns to validate")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Rule-specific parameters")
    
    thresholds: Optional[List[ThresholdSchema]] = Field(None, description="Validation thresholds")
    
    severity: Optional[str] = Field(None, description="Rule severity: error, warning, info")
    tags: Optional[List[str]] = Field(None, description="Rule tags")
    
    class Config:
        use_enum_values = True


class RuleResponse(BaseModel):
    """Response schema for rule data."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    rule_type: str = Field(..., description="Type of validation rule")
    enabled: bool = Field(..., description="Whether rule is active")
    
    target_columns: List[str] = Field(default_factory=list, description="Columns to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific parameters")
    
    thresholds: List[ThresholdSchema] = Field(
        default_factory=list, 
        description="Validation thresholds"
    )
    
    severity: str = Field(..., description="Rule severity")
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    
    class Config:
        use_enum_values = True


class RuleListResponse(BaseModel):
    """Response schema for list of rules."""
    
    version: str = Field(..., description="Configuration version")
    total_rules: int = Field(..., description="Total number of rules")
    enabled_rules: int = Field(..., description="Number of enabled rules")
    disabled_rules: int = Field(..., description="Number of disabled rules")
    rules: List[RuleResponse] = Field(..., description="List of rules")


class RuleExecutionRequest(BaseModel):
    """Request schema for executing rules."""
    
    dataset_name: str = Field(..., description="Name of dataset to validate")
    rule_ids: Optional[List[str]] = Field(None, description="Specific rule IDs to execute. If None, executes all enabled rules")


class ThresholdEvaluationResult(BaseModel):
    """Result of threshold evaluation."""
    
    metric: str = Field(..., description="Metric name")
    operator: str = Field(..., description="Comparison operator")
    expected: float = Field(..., description="Expected threshold value")
    actual: float = Field(..., description="Actual metric value")
    passed: bool = Field(..., description="Whether threshold was met")


class RuleExecutionResult(BaseModel):
    """Result of rule execution."""
    
    rule_id: str = Field(..., description="Rule identifier")
    rule_name: str = Field(..., description="Rule name")
    status: str = Field(..., description="Validation status")
    passed: bool = Field(..., description="Whether validation passed")
    
    total_records: int = Field(0, description="Total records validated")
    failed_records: int = Field(0, description="Failed records")
    pass_rate: float = Field(0.0, description="Pass rate percentage")
    
    message: str = Field("", description="Validation message")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    
    threshold_evaluations: List[ThresholdEvaluationResult] = Field(
        default_factory=list,
        description="Threshold evaluation results"
    )
    
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RuleExecutionResponse(BaseModel):
    """Response schema for rule execution."""
    
    dataset_name: str = Field(..., description="Dataset name")
    total_rules_executed: int = Field(..., description="Total rules executed")
    passed_rules: int = Field(..., description="Rules that passed")
    failed_rules: int = Field(..., description="Rules that failed")
    overall_passed: bool = Field(..., description="Overall validation status")
    
    results: List[RuleExecutionResult] = Field(..., description="Individual rule results")
    
    execution_timestamp: datetime = Field(
        default_factory=datetime.utcnow, 
        description="When execution started"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RuleToggleRequest(BaseModel):
    """Request to enable/disable a rule."""
    
    enabled: bool = Field(..., description="Enable (true) or disable (false) the rule")


class RuleToggleResponse(BaseModel):
    """Response after toggling rule status."""
    
    rule_id: str = Field(..., description="Rule identifier")
    enabled: bool = Field(..., description="Current enabled status")
    message: str = Field(..., description="Success message")
