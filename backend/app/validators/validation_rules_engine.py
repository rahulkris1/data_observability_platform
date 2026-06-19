"""Validation Rules Engine.

Load validation rules from JSON configuration and execute them against datasets.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from pyspark.sql import DataFrame

from app.validators.rules_parser import (
    RuleDefinition, 
    RulesConfiguration, 
    RuleType,
    parse_rules_from_dict
)
from app.validators.base_validator import ValidationResult, ValidationStatus
from app.validators.null_validator import NullValidator
from app.validators.datatype_validator import DatatypeValidator
from app.validators.schema_validator import SchemaValidator
from app.validators.referential_integrity_validator import ReferentialIntegrityValidator


class ValidationRulesEngine:
    """
    Engine for loading and executing validation rules from JSON configuration.
    
    Supports dynamic rule loading, threshold evaluation, and rule enable/disable.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the validation rules engine.
        
        Args:
            config_path: Path to JSON rules configuration file
        """
        self.config_path = config_path
        self.rules_config: Optional[RulesConfiguration] = None
        
        if config_path:
            self.load_rules(config_path)
    
    def load_rules(self, config_path: str) -> RulesConfiguration:
        """
        Load validation rules from JSON configuration file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            Loaded RulesConfiguration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Rules configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            
            self.rules_config = parse_rules_from_dict(config_dict)
            self.config_path = config_path
            
            return self.rules_config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in rules configuration: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load rules configuration: {str(e)}")
    
    def load_rules_from_dict(self, config_dict: Dict[str, Any]) -> RulesConfiguration:
        """
        Load validation rules from dictionary.
        
        Args:
            config_dict: Dictionary containing rules configuration
            
        Returns:
            Loaded RulesConfiguration
        """
        self.rules_config = parse_rules_from_dict(config_dict)
        return self.rules_config
    
    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get all enabled rules."""
        if not self.rules_config:
            return []
        return self.rules_config.get_enabled_rules()
    
    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        """
        Get a specific rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            RuleDefinition if found, None otherwise
        """
        if not self.rules_config:
            return None
        return self.rules_config.get_rule_by_id(rule_id)
    
    def enable_rule(self, rule_id: str) -> bool:
        """
        Enable a rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            True if rule was found and enabled, False otherwise
        """
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """
        Disable a rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            True if rule was found and disabled, False otherwise
        """
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False
    
    def execute_rule(
        self, 
        rule: RuleDefinition, 
        df: DataFrame,
        dataset_name: str
    ) -> ValidationResult:
        """
        Execute a single validation rule against a DataFrame.
        
        Args:
            rule: Rule definition to execute
            df: DataFrame to validate
            dataset_name: Name of the dataset being validated
            
        Returns:
            ValidationResult from rule execution
        """
        start_time = datetime.utcnow()
        
        try:
            # Skip if rule is disabled
            if not rule.enabled:
                return ValidationResult(
                    validator_name=rule.name,
                    status=ValidationStatus.PASSED,
                    passed=True,
                    message=f"Rule {rule.rule_id} is disabled",
                    details={"rule_id": rule.rule_id, "enabled": False}
                )
            
            # Execute based on rule type
            result = self._execute_by_type(rule, df, dataset_name)
            
            # Evaluate thresholds
            if rule.thresholds:
                threshold_results = self._evaluate_thresholds(rule, result)
                result.details["threshold_evaluation"] = threshold_results
                
                # Update status based on threshold evaluation
                if not all(t["passed"] for t in threshold_results):
                    result.status = ValidationStatus.FAILED
                    result.passed = False
                    failed_thresholds = [t for t in threshold_results if not t["passed"]]
                    result.message += f" | Threshold violations: {len(failed_thresholds)}"
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ValidationResult(
                validator_name=rule.name,
                status=ValidationStatus.ERROR,
                passed=False,
                message=f"Error executing rule: {str(e)}",
                errors=[str(e)],
                details={"rule_id": rule.rule_id, "error": str(e)},
                execution_time_ms=execution_time
            )
    
    def _execute_by_type(
        self, 
        rule: RuleDefinition, 
        df: DataFrame,
        dataset_name: str
    ) -> ValidationResult:
        """Execute rule based on its type."""
        
        if rule.rule_type == RuleType.NULL_CHECK:
            validator = NullValidator()
            return self._execute_null_check(validator, rule, df)
        
        elif rule.rule_type == RuleType.DATATYPE:
            validator = DatatypeValidator()
            return self._execute_datatype_check(validator, rule, df)
        
        elif rule.rule_type == RuleType.REFERENTIAL_INTEGRITY:
            validator = ReferentialIntegrityValidator()
            return self._execute_referential_integrity(validator, rule, df)
        
        elif rule.rule_type == RuleType.RANGE:
            return self._execute_range_check(rule, df)
        
        elif rule.rule_type == RuleType.PATTERN:
            return self._execute_pattern_check(rule, df)
        
        elif rule.rule_type == RuleType.UNIQUENESS:
            return self._execute_uniqueness_check(rule, df)
        
        else:
            return ValidationResult(
                validator_name=rule.name,
                status=ValidationStatus.ERROR,
                passed=False,
                message=f"Unsupported rule type: {rule.rule_type}",
                details={"rule_id": rule.rule_id, "rule_type": rule.rule_type}
            )
    
    def _execute_null_check(
        self, 
        validator: NullValidator, 
        rule: RuleDefinition, 
        df: DataFrame
    ) -> ValidationResult:
        """Execute null check validation."""
        columns = rule.target_columns
        if not columns:
            columns = df.columns
        
        return validator.validate(df, columns)
    
    def _execute_datatype_check(
        self, 
        validator: DatatypeValidator, 
        rule: RuleDefinition, 
        df: DataFrame
    ) -> ValidationResult:
        """Execute datatype validation."""
        expected_types = rule.parameters.get("expected_types", {})
        return validator.validate(df, expected_types)
    
    def _execute_referential_integrity(
        self, 
        validator: ReferentialIntegrityValidator, 
        rule: RuleDefinition, 
        df: DataFrame
    ) -> ValidationResult:
        """Execute referential integrity validation."""
        reference_df = rule.parameters.get("reference_df")
        source_column = rule.parameters.get("source_column")
        reference_column = rule.parameters.get("reference_column")
        
        if not all([reference_df, source_column, reference_column]):
            return ValidationResult(
                validator_name=rule.name,
                status=ValidationStatus.ERROR,
                passed=False,
                message="Missing required parameters for referential integrity check",
                details={"rule_id": rule.rule_id}
            )
        
        return validator.validate(df, reference_df, source_column, reference_column)
    
    def _execute_range_check(self, rule: RuleDefinition, df: DataFrame) -> ValidationResult:
        """Execute range validation."""
        # Placeholder for range validation
        return ValidationResult(
            validator_name=rule.name,
            status=ValidationStatus.PASSED,
            passed=True,
            message="Range validation placeholder",
            details={"rule_id": rule.rule_id, "type": "range"}
        )
    
    def _execute_pattern_check(self, rule: RuleDefinition, df: DataFrame) -> ValidationResult:
        """Execute pattern validation."""
        # Placeholder for pattern validation
        return ValidationResult(
            validator_name=rule.name,
            status=ValidationStatus.PASSED,
            passed=True,
            message="Pattern validation placeholder",
            details={"rule_id": rule.rule_id, "type": "pattern"}
        )
    
    def _execute_uniqueness_check(self, rule: RuleDefinition, df: DataFrame) -> ValidationResult:
        """Execute uniqueness validation."""
        # Placeholder for uniqueness validation
        return ValidationResult(
            validator_name=rule.name,
            status=ValidationStatus.PASSED,
            passed=True,
            message="Uniqueness validation placeholder",
            details={"rule_id": rule.rule_id, "type": "uniqueness"}
        )
    
    def _evaluate_thresholds(
        self, 
        rule: RuleDefinition, 
        result: ValidationResult
    ) -> List[Dict[str, Any]]:
        """
        Evaluate thresholds against validation result.
        
        Args:
            rule: Rule definition with thresholds
            result: Validation result to evaluate
            
        Returns:
            List of threshold evaluation results
        """
        threshold_results = []
        
        for threshold in rule.thresholds:
            # Get actual value from result
            actual_value = None
            
            if threshold.metric == "pass_rate":
                actual_value = result.pass_rate
            elif threshold.metric == "failed_records":
                actual_value = float(result.failed_records)
            elif threshold.metric == "total_records":
                actual_value = float(result.total_records)
            
            if actual_value is not None:
                passed = threshold.evaluate(actual_value)
                threshold_results.append({
                    "metric": threshold.metric,
                    "operator": threshold.operator.value,
                    "expected": threshold.value,
                    "actual": actual_value,
                    "passed": passed
                })
        
        return threshold_results
    
    def execute_all_rules(
        self, 
        df: DataFrame, 
        dataset_name: str
    ) -> List[ValidationResult]:
        """
        Execute all enabled rules against a DataFrame.
        
        Args:
            df: DataFrame to validate
            dataset_name: Name of the dataset being validated
            
        Returns:
            List of ValidationResults for each rule
        """
        results = []
        enabled_rules = self.get_enabled_rules()
        
        for rule in enabled_rules:
            result = self.execute_rule(rule, df, dataset_name)
            results.append(result)
        
        return results
    
    def save_rules(self, output_path: Optional[str] = None) -> str:
        """
        Save current rules configuration to JSON file.
        
        Args:
            output_path: Path to save configuration. If None, uses current config_path
            
        Returns:
            Path where configuration was saved
            
        Raises:
            ValueError: If no configuration is loaded
        """
        if not self.rules_config:
            raise ValueError("No rules configuration loaded")
        
        save_path = output_path or self.config_path
        if not save_path:
            raise ValueError("No output path specified")
        
        config_dict = self.rules_config.dict()
        
        with open(save_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        return save_path
