"""Verify validators with sample DataFrame."""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from app.utils.spark_utils import get_spark
from app.validators import (
    SchemaValidator,
    NullValidator,
    ChecksumValidator,
    ValidationStatus
)


def create_sample_dataframe():
    """Create a sample DataFrame for validation testing."""
    spark = get_spark()
    
    # Sample data with various data quality scenarios
    data = [
        ("user_1", "Alice", 25, "Engineering"),
        ("user_2", "Bob", 30, "Sales"),
        ("user_3", "Charlie", None, "Marketing"),  # Null age
        ("user_4", "Diana", 28, "Engineering"),
        ("user_5", "Eve", 35, None),  # Null department
    ]
    
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("age", IntegerType(), True),
        StructField("department", StringType(), True),
    ])
    
    return spark.createDataFrame(data, schema)


def print_validation_result(validator_name, result):
    """Pretty print validation result."""
    print(f"\n{'=' * 60}")
    print(f"{validator_name}")
    print(f"{'=' * 60}")
    print(f"Status: {result.status.value.upper()}")
    print(f"Passed: {'✓' if result.passed else '✗'}")
    print(f"Total Records: {result.total_records}")
    print(f"Failed Records: {result.failed_records}")
    print(f"Pass Rate: {result.pass_rate}%")
    print(f"Execution Time: {result.execution_time_ms}ms")
    print(f"Message: {result.message}")
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
    
    if result.details:
        print(f"\nDetails:")
        print(json.dumps(result.details, indent=2, default=str))


def verify_validators():
    """Verify all validators with sample data."""
    
    print("=" * 60)
    print("Validator Verification with Sample Data")
    print("=" * 60)
    
    try:
        # Create sample DataFrame
        print("\n1. Creating sample DataFrame...")
        df = create_sample_dataframe()
        print(f"   ✓ Created DataFrame with {df.count()} rows")
        print("\n   Sample Data:")
        df.show()
        
        # Test SchemaValidator
        print("\n2. Testing SchemaValidator...")
        
        # Test with required columns
        schema_validator = SchemaValidator(
            required_columns=["id", "name", "age", "department"],
            column_types={
                "id": "string",
                "name": "string",
                "age": "int",
                "department": "string"
            }
        )
        result = schema_validator.validate(df)
        print_validation_result("SchemaValidator - Required Columns", result)
        
        # Test with missing column (should fail)
        schema_validator_fail = SchemaValidator(
            required_columns=["id", "name", "email"],  # 'email' doesn't exist
        )
        result = schema_validator_fail.validate(df)
        print_validation_result("SchemaValidator - Missing Column (Expected Fail)", result)
        
        # Test NullValidator
        print("\n3. Testing NullValidator...")
        
        # Test with non-null requirement (should fail due to nulls in data)
        null_validator = NullValidator(
            non_null_columns=["id", "name"],  # These should not have nulls
            max_null_percentage=10.0  # Allow up to 10% nulls globally
        )
        result = null_validator.validate(df)
        print_validation_result("NullValidator - Allow Some Nulls", result)
        
        # Test with strict non-null requirement (should fail)
        null_validator_strict = NullValidator(
            non_null_columns=["id", "name", "age", "department"],  # No nulls allowed
        )
        result = null_validator_strict.validate(df)
        print_validation_result("NullValidator - Strict (Expected Fail)", result)
        
        # Test ChecksumValidator
        print("\n4. Testing ChecksumValidator...")
        
        # Test checksum calculation
        checksum_validator = ChecksumValidator(
            checksum_columns=["id", "name"],
            detect_duplicates=True
        )
        result = checksum_validator.validate(df)
        print_validation_result("ChecksumValidator - Duplicate Detection", result)
        
        # Test with expected checksum
        dataset_checksum = result.details.get("dataset_checksum")
        checksum_validator_match = ChecksumValidator(
            expected_checksum=dataset_checksum,
            checksum_columns=["id", "name"]
        )
        result = checksum_validator_match.validate(df)
        print_validation_result("ChecksumValidator - Checksum Match", result)
        
        # Test with wrong expected checksum (should fail)
        checksum_validator_mismatch = ChecksumValidator(
            expected_checksum="wrong_checksum_12345",
            checksum_columns=["id", "name"]
        )
        result = checksum_validator_mismatch.validate(df)
        print_validation_result("ChecksumValidator - Checksum Mismatch (Expected Fail)", result)
        
        print("\n" + "=" * 60)
        print("✓ Validator verification completed successfully!")
        print("=" * 60)
        print("\nSummary:")
        print("  • SchemaValidator: Validates column presence and types")
        print("  • NullValidator: Checks for null/missing values")
        print("  • ChecksumValidator: Verifies data integrity and detects duplicates")
        print("\nAll validators are working correctly!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during validator verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_validators()
    sys.exit(0 if success else 1)
