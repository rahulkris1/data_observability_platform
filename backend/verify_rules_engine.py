"""
Verify Rules Engine Implementation

Test script to verify the validation rules engine works correctly
with sample configurations.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from datetime import datetime

from app.validators.validation_rules_engine import ValidationRulesEngine
from app.validators.rules_parser import RulesConfiguration


def create_test_spark_session():
    """Create a test Spark session."""
    return SparkSession.builder \
        .appName("RulesEngineTest") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def create_sample_dataframe(spark):
    """Create a sample DataFrame for testing."""
    schema = StructType([
        StructField("customer_id", IntegerType(), True),
        StructField("email", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("created_at", TimestampType(), True),
    ])
    
    data = [
        (1, "user1@example.com", 25, datetime.now()),
        (2, "user2@example.com", 30, datetime.now()),
        (3, None, 35, datetime.now()),  # Missing email
        (4, "user4@example.com", None, datetime.now()),  # Missing age
        (5, "user5@example.com", 40, datetime.now()),
    ]
    
    return spark.createDataFrame(data, schema)


def test_load_rules_from_config():
    """Test loading rules from JSON configuration."""
    print("\n" + "="*70)
    print("TEST 1: Load Rules from Configuration File")
    print("="*70)
    
    config_path = "backend/config/validation_rules.json"
    
    if not Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        engine = ValidationRulesEngine(config_path)
        
        if not engine.rules_config:
            print("❌ Failed to load rules configuration")
            return False
        
        print(f"✓ Loaded {len(engine.rules_config.rules)} rules")
        print(f"  - Version: {engine.rules_config.version}")
        print(f"  - Enabled rules: {len(engine.get_enabled_rules())}")
        
        # Display rule summary
        for rule in engine.rules_config.rules:
            status = "✓ Enabled" if rule.enabled else "✗ Disabled"
            print(f"  - {rule.rule_id}: {rule.name} ({status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading rules: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_rules_from_dict():
    """Test loading rules from dictionary."""
    print("\n" + "="*70)
    print("TEST 2: Load Rules from Dictionary")
    print("="*70)
    
    test_config = {
        "version": "1.0",
        "rules": [
            {
                "rule_id": "test_rule_1",
                "name": "Test Null Check",
                "description": "Test null validation",
                "rule_type": "null_check",
                "enabled": True,
                "target_columns": ["customer_id", "email"],
                "parameters": {},
                "thresholds": [
                    {
                        "metric": "pass_rate",
                        "operator": ">=",
                        "value": 95.0
                    }
                ],
                "severity": "error",
                "tags": ["test"]
            }
        ]
    }
    
    try:
        engine = ValidationRulesEngine()
        engine.load_rules_from_dict(test_config)
        
        print(f"✓ Successfully loaded {len(engine.rules_config.rules)} rule(s)")
        
        rule = engine.get_rule("test_rule_1")
        if rule:
            print(f"  - Rule ID: {rule.rule_id}")
            print(f"  - Name: {rule.name}")
            print(f"  - Type: {rule.rule_type}")
            print(f"  - Enabled: {rule.enabled}")
            print(f"  - Thresholds: {len(rule.thresholds)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading rules from dict: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enable_disable_rules():
    """Test enabling and disabling rules."""
    print("\n" + "="*70)
    print("TEST 3: Enable/Disable Rules")
    print("="*70)
    
    test_config = {
        "version": "1.0",
        "rules": [
            {
                "rule_id": "toggle_test",
                "name": "Toggle Test Rule",
                "rule_type": "null_check",
                "enabled": True,
                "target_columns": [],
                "parameters": {},
                "thresholds": [],
                "severity": "error",
                "tags": []
            }
        ]
    }
    
    try:
        engine = ValidationRulesEngine()
        engine.load_rules_from_dict(test_config)
        
        rule = engine.get_rule("toggle_test")
        print(f"  Initial state: {'Enabled' if rule.enabled else 'Disabled'}")
        
        # Disable
        engine.disable_rule("toggle_test")
        rule = engine.get_rule("toggle_test")
        if not rule.enabled:
            print(f"  ✓ Successfully disabled rule")
        else:
            print(f"  ❌ Failed to disable rule")
            return False
        
        # Enable
        engine.enable_rule("toggle_test")
        rule = engine.get_rule("toggle_test")
        if rule.enabled:
            print(f"  ✓ Successfully enabled rule")
        else:
            print(f"  ❌ Failed to enable rule")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error toggling rules: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_null_check_rule():
    """Test executing a null check rule against a DataFrame."""
    print("\n" + "="*70)
    print("TEST 4: Execute Null Check Rule")
    print("="*70)
    
    test_config = {
        "version": "1.0",
        "rules": [
            {
                "rule_id": "null_test",
                "name": "Null Check Test",
                "rule_type": "null_check",
                "enabled": True,
                "target_columns": ["customer_id", "email"],
                "parameters": {},
                "thresholds": [
                    {
                        "metric": "pass_rate",
                        "operator": ">=",
                        "value": 80.0
                    }
                ],
                "severity": "error",
                "tags": ["test"]
            }
        ]
    }
    
    try:
        # Create Spark session and sample data
        spark = create_test_spark_session()
        df = create_sample_dataframe(spark)
        
        print(f"  Created test DataFrame with {df.count()} rows")
        
        # Load and execute rule
        engine = ValidationRulesEngine()
        engine.load_rules_from_dict(test_config)
        
        rule = engine.get_rule("null_test")
        result = engine.execute_rule(rule, df, "test_dataset")
        
        print(f"  ✓ Rule executed successfully")
        print(f"    - Status: {result.status.value}")
        print(f"    - Passed: {result.passed}")
        print(f"    - Total records: {result.total_records}")
        print(f"    - Failed records: {result.failed_records}")
        print(f"    - Pass rate: {result.pass_rate:.2f}%")
        print(f"    - Message: {result.message}")
        
        if result.details.get("threshold_evaluation"):
            print(f"    - Threshold evaluations:")
            for threshold_result in result.details["threshold_evaluation"]:
                status_icon = "✓" if threshold_result["passed"] else "✗"
                print(f"      {status_icon} {threshold_result['metric']} {threshold_result['operator']} {threshold_result['expected']} (actual: {threshold_result['actual']})")
        
        spark.stop()
        return True
        
    except Exception as e:
        print(f"❌ Error executing rule: {e}")
        import traceback
        traceback.print_exc()
        try:
            spark.stop()
        except:
            pass
        return False


def test_execute_all_enabled_rules():
    """Test executing all enabled rules."""
    print("\n" + "="*70)
    print("TEST 5: Execute All Enabled Rules")
    print("="*70)
    
    config_path = "backend/config/validation_rules.json"
    
    if not Path(config_path).exists():
        print(f"⚠ Configuration file not found: {config_path}, skipping test")
        return True
    
    try:
        # Create Spark session and sample data
        spark = create_test_spark_session()
        df = create_sample_dataframe(spark)
        
        # Load and execute all enabled rules
        engine = ValidationRulesEngine(config_path)
        enabled_rules = engine.get_enabled_rules()
        
        print(f"  Executing {len(enabled_rules)} enabled rule(s)")
        
        results = engine.execute_all_rules(df, "test_dataset")
        
        print(f"  ✓ Executed {len(results)} rule(s)")
        
        for i, result in enumerate(results, 1):
            status_icon = "✓" if result.passed else "✗"
            print(f"    {status_icon} Rule {i}: {result.validator_name}")
            print(f"       Status: {result.status.value}, Pass Rate: {result.pass_rate:.2f}%")
        
        spark.stop()
        return True
        
    except Exception as e:
        print(f"❌ Error executing rules: {e}")
        import traceback
        traceback.print_exc()
        try:
            spark.stop()
        except:
            pass
        return False


def test_threshold_evaluation():
    """Test threshold evaluation logic."""
    print("\n" + "="*70)
    print("TEST 6: Threshold Evaluation")
    print("="*70)
    
    from app.validators.rules_parser import ValidationThreshold, ThresholdOperator
    
    test_cases = [
        (ValidationThreshold(metric="pass_rate", operator=ThresholdOperator.GREATER_THAN, value=90.0), 95.0, True),
        (ValidationThreshold(metric="pass_rate", operator=ThresholdOperator.GREATER_THAN, value=90.0), 85.0, False),
        (ValidationThreshold(metric="pass_rate", operator=ThresholdOperator.GREATER_THAN_EQUAL, value=90.0), 90.0, True),
        (ValidationThreshold(metric="failed_records", operator=ThresholdOperator.LESS_THAN, value=10.0), 5.0, True),
        (ValidationThreshold(metric="failed_records", operator=ThresholdOperator.LESS_THAN, value=10.0), 15.0, False),
    ]
    
    all_passed = True
    
    for threshold, actual_value, expected_result in test_cases:
        result = threshold.evaluate(actual_value)
        status = "✓" if result == expected_result else "✗"
        
        if result != expected_result:
            all_passed = False
        
        print(f"  {status} {threshold.metric} {threshold.operator.value} {threshold.value} with actual={actual_value} -> {result}")
    
    if all_passed:
        print(f"\n  ✓ All threshold tests passed")
    else:
        print(f"\n  ❌ Some threshold tests failed")
    
    return all_passed


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print("VALIDATION RULES ENGINE VERIFICATION")
    print("="*70)
    
    tests = [
        ("Load Rules from Config", test_load_rules_from_config),
        ("Load Rules from Dict", test_load_rules_from_dict),
        ("Enable/Disable Rules", test_enable_disable_rules),
        ("Execute Null Check Rule", test_execute_null_check_rule),
        ("Execute All Enabled Rules", test_execute_all_enabled_rules),
        ("Threshold Evaluation", test_threshold_evaluation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  ✓ All tests passed!")
        return 0
    else:
        print(f"\n  ❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
