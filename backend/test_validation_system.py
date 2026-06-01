"""
Test script to verify validation aggregation and logging functionality

This script tests:
1. Creating validators
2. Running validation aggregation
3. Logging validation results to PostgreSQL
4. Retrieving validation metrics and history

Run this script after database migrations are applied.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, BooleanType
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.validators import (
    SchemaValidator,
    NullValidator,
    DatatypeValidator,
    ColumnExistenceValidator,
    ChecksumValidator
)
from app.services.validation_aggregator import ValidationAggregator
from app.services.validation_log_service import ValidationLogService


def create_test_dataframe(spark: SparkSession):
    """Create a test DataFrame with sample data"""
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("salary", FloatType(), True),
        StructField("is_active", BooleanType(), True),
    ])
    
    data = [
        (1, "Alice", "alice@example.com", 30, 75000.0, True),
        (2, "Bob", "bob@example.com", None, 80000.0, True),
        (3, "Charlie", "charlie@example.com", 35, 90000.0, False),
        (4, None, "dave@example.com", 28, 70000.0, True),
        (5, "Eve", "eve@example.com", 42, None, True),
    ]
    
    return spark.createDataFrame(data, schema)


def test_validation_aggregation():
    """Test validation aggregation with multiple validators"""
    print("\n" + "=" * 80)
    print("TESTING VALIDATION AGGREGATION")
    print("=" * 80)
    
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("ValidationAggregationTest") \
        .master("local[*]") \
        .getOrCreate()
    
    try:
        # Create test DataFrame
        print("\n1. Creating test DataFrame...")
        df = create_test_dataframe(spark)
        print(f"   ✓ Created DataFrame with {df.count()} rows and {len(df.columns)} columns")
        df.show()
        
        # Create validation aggregator
        print("\n2. Setting up validation aggregator...")
        aggregator = ValidationAggregator()
        
        # Add validators
        print("\n3. Adding validators...")
        
        # Column existence validator
        aggregator.add_validator(
            ColumnExistenceValidator(
                required_columns=["id", "name", "email", "age", "salary", "is_active"]
            )
        )
        print("   ✓ Added ColumnExistenceValidator")
        
        # Schema validator
        aggregator.add_validator(
            SchemaValidator(
                column_types={
                    "id": "int",
                    "name": "string",
                    "email": "string",
                    "age": "int",
                    "salary": "double",
                    "is_active": "boolean"
                }
            )
        )
        print("   ✓ Added SchemaValidator")
        
        # Null validator
        aggregator.add_validator(
            NullValidator(
                max_null_percentage=20.0,  # Allow up to 20% nulls
                non_null_columns=["id", "email"]
            )
        )
        print("   ✓ Added NullValidator")
        
        # Datatype validator
        aggregator.add_validator(
            DatatypeValidator(
                column_types={
                    "id": "integer",
                    "name": "string",
                    "email": "string",
                    "age": "integer",
                    "salary": "float",
                    "is_active": "boolean"
                }
            )
        )
        print("   ✓ Added DatatypeValidator")
        
        # Execute validation
        print("\n4. Executing validation aggregation...")
        summary = aggregator.validate(df, dataset_name="test_dataset")
        
        # Display results
        print("\n" + "-" * 80)
        print("VALIDATION SUMMARY")
        print("-" * 80)
        print(f"Dataset: {summary.dataset_name}")
        print(f"Validation Timestamp: {summary.validation_timestamp}")
        print(f"Overall Status: {summary.overall_status}")
        print(f"Overall Passed: {summary.overall_passed}")
        print(f"\nValidator Counts:")
        print(f"  Total: {summary.total_validators}")
        print(f"  Passed: {summary.passed_validators}")
        print(f"  Failed: {summary.failed_validators}")
        print(f"  Warnings: {summary.warning_validators}")
        print(f"  Errors: {summary.error_validators}")
        print(f"\nExecution Time: {summary.total_execution_time_ms:.2f}ms")
        
        print("\n" + "-" * 80)
        print("INDIVIDUAL VALIDATOR RESULTS")
        print("-" * 80)
        for validator_result in summary.validators:
            print(f"\n{validator_result.validator_name}:")
            print(f"  Status: {validator_result.status}")
            print(f"  Passed: {validator_result.passed}")
            print(f"  Pass Rate: {validator_result.pass_rate:.2f}%")
            print(f"  Message: {validator_result.message}")
            if validator_result.errors:
                print(f"  Errors: {', '.join(validator_result.errors)}")
        
        return summary
        
    finally:
        spark.stop()


def test_validation_logging(summary):
    """Test logging validation results to PostgreSQL"""
    print("\n" + "=" * 80)
    print("TESTING VALIDATION LOGGING")
    print("=" * 80)
    
    db: Session = SessionLocal()
    
    try:
        # Create validation log service
        print("\n1. Creating ValidationLogService...")
        log_service = ValidationLogService(db)
        print("   ✓ Service created")
        
        # Log the validation summary
        print("\n2. Logging validation summary to database...")
        log_entries = log_service.log_validation_summary(summary)
        print(f"   ✓ Created {len(log_entries)} log entries")
        
        # Retrieve validation history
        print("\n3. Retrieving validation history...")
        history = log_service.get_validation_history(limit=10)
        print(f"   ✓ Retrieved {len(history)} history items")
        
        print("\n" + "-" * 80)
        print("VALIDATION HISTORY")
        print("-" * 80)
        for item in history:
            print(f"\nID: {item.id}")
            print(f"  Dataset: {item.dataset_name}")
            print(f"  Type: {item.validation_type}")
            print(f"  Status: {item.status}")
            print(f"  Pass Rate: {item.pass_rate:.2f}%")
            print(f"  Executed: {item.executed_at}")
        
        # Get validation metrics
        print("\n4. Retrieving validation metrics...")
        metrics = log_service.get_validation_metrics(dataset_name="test_dataset")
        print("   ✓ Metrics retrieved")
        
        print("\n" + "-" * 80)
        print("VALIDATION METRICS")
        print("-" * 80)
        print(f"Total Validations: {metrics.total_validations}")
        print(f"Passed: {metrics.passed_validations}")
        print(f"Failed: {metrics.failed_validations}")
        print(f"Warnings: {metrics.warning_validations}")
        print(f"Average Pass Rate: {metrics.average_pass_rate:.2f}%")
        
        # Get dataset statistics
        print("\n5. Retrieving dataset statistics...")
        stats = log_service.get_dataset_statistics("test_dataset")
        print("   ✓ Statistics retrieved")
        
        print("\n" + "-" * 80)
        print("DATASET STATISTICS")
        print("-" * 80)
        print(f"Dataset: {stats['dataset_name']}")
        print(f"Row Count: {stats['row_count']}")
        print(f"Column Count: {stats['column_count']}")
        print(f"Validation Score: {stats['validation_score']:.2f}%")
        print(f"Last Validated: {stats['last_validated']}")
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during validation logging: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "VALIDATION SYSTEM TEST SUITE" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Test validation aggregation
        summary = test_validation_aggregation()
        
        # Test validation logging
        test_validation_logging(summary)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
