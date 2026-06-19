"""Rules Parser for validation rule definitions.

Parse and validate rule configurations from JSON.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class RuleType(str, Enum):
    """Supported validation rule types."""
    NULL_CHECK = "null_check"
    DATATYPE = "datatype"
    RANGE = "range"
    PATTERN = "pattern"
    UNIQUENESS = "uniqueness"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    CUSTOM = "custom"


class ThresholdOperator(str, Enum):
    """Threshold comparison operators."""
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


class ValidationThreshold(BaseModel):
    """Configurable validation threshold."""
    
    metric: str = Field(..., description="Metric name (e.g., 'pass_rate', 'failed_records')")
    operator: ThresholdOperator = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")
    
    def evaluate(self, actual_value: float) -> bool:
        """Evaluate if actual value meets threshold."""
        if self.operator == ThresholdOperator.GREATER_THAN:
            return actual_value > self.value
        elif self.operator == ThresholdOperator.GREATER_THAN_EQUAL:
            return actual_value >= self.value
        elif self.operator == ThresholdOperator.LESS_THAN:
            return actual_value < self.value
        elif self.operator == ThresholdOperator.LESS_THAN_EQUAL:
            return actual_value <= self.value
        elif self.operator == ThresholdOperator.EQUAL:
            return actual_value == self.value
        elif self.operator == ThresholdOperator.NOT_EQUAL:
            return actual_value != self.value
        return False


class RuleDefinition(BaseModel):
    """Parsed validation rule definition."""
    
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    rule_type: RuleType = Field(..., description="Type of validation rule")
    enabled: bool = Field(True, description="Whether rule is active")
    
    # Rule configuration
    target_columns: List[str] = Field(default_factory=list, description="Columns to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific parameters")
    
    # Thresholds
    thresholds: List[ValidationThreshold] = Field(
        default_factory=list, 
        description="Validation thresholds to enforce"
    )
    
    # Metadata
    severity: str = Field("error", description="Rule severity: error, warning, info")
    tags: List[str] = Field(default_factory=list, description="Rule tags for categorization")
    
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
    
    @validator('severity')
    def validate_severity(cls, v):
        """Ensure severity is valid."""
        valid_severities = ['error', 'warning', 'info']
        if v.lower() not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}")
        return v.lower()


class RulesConfiguration(BaseModel):
    """Container for multiple rule definitions."""
    
    version: str = Field("1.0", description="Configuration version")
    rules: List[RuleDefinition] = Field(default_factory=list, description="List of rule definitions")
    
    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get only enabled rules."""
        return [rule for rule in self.rules if rule.enabled]
    
    def get_rule_by_id(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get a rule by its ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[RuleDefinition]:
        """Get all rules of a specific type."""
        return [rule for rule in self.rules if rule.rule_type == rule_type]
    
    def get_rules_by_tag(self, tag: str) -> List[RuleDefinition]:
        """Get all rules with a specific tag."""
        return [rule for rule in self.rules if tag in rule.tags]


def parse_rules_from_dict(config_dict: Dict[str, Any]) -> RulesConfiguration:
    """
    Parse rules configuration from dictionary.
    
    Args:
        config_dict: Dictionary containing rules configuration
        
    Returns:
        Parsed RulesConfiguration object
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        return RulesConfiguration(**config_dict)
    except Exception as e:
        raise ValueError(f"Failed to parse rules configuration: {str(e)}")


def validate_rule_definition(rule_dict: Dict[str, Any]) -> RuleDefinition:
    """
    Validate a single rule definition.
    
    Args:
        rule_dict: Dictionary containing rule definition
        
    Returns:
        Parsed and validated RuleDefinition
        
    Raises:
        ValueError: If rule definition is invalid
    """
    try:
        return RuleDefinition(**rule_dict)
    except Exception as e:
        raise ValueError(f"Invalid rule definition: {str(e)}")
