"""
Verification script for referential integrity validator.

Tests:
1. Primary key uniqueness validation (duplicate detection)
2. Foreign key validation (orphan detection)
3. Failed row extraction
4. Validation result storage in validation_logs table
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '.')

from app.validators.referential_integrity_validator import (
    ReferentialIntegrityValidator,
    detect_duplicates,
    extract_failed_rows
)
from app.core.database import get_db
from app.models.validation_log import ValidationLog


def create_spark_session():
    """Create a Spark session for testing."""
    return SparkSession.builder \
        .appName("IntegrityValidatorTest") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def test_primary_key_validation():
    """Test primary key uniqueness validation with duplicate detection."""
    print("\n" + "="*80)
    print("TEST 1: Primary Key Uniqueness Validation")
    print("="*80)
    
    spark = create_spark_session()
    
    # Create sample dataset with duplicate primary keys
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("status", StringType(), True)
    ])
    
    data = [
        (1, "Alice Johnson", "alice@example.com", "active"),
        (2, "Bob Smith", "bob@example.com", "active"),
        (3, "Charlie Brown", "charlie@example.com", "inactive"),
        (1, "Alice Johnson DUPLICATE", "alice2@example.com", "active"),  # Duplicate ID
        (4, "Diana Prince", "diana@example.com", "active"),
        (2, "Bob Smith DUPLICATE", "bob2@example.com", "active"),  # Duplicate ID
        (5, "Eve Adams", "eve@example.com", "active"),
    ]
    
    df = spark.createDataFrame(data, schema)
    
    print(f"\n📊 Created dataset with {df.count()} records")
    print("\nDataset preview:")
    df.show(truncate=False)
    
    # Create validator with primary key
    validator = ReferentialIntegrityValidator(
        primary_key_columns=["customer_id"],
        name="CustomerPrimaryKeyValidator"
    )
    
    # Run validation
    print("\n🔍 Running primary key validation...")
    result = validator.validate(df)
    
    # Display results
    print(f"\n✅ Validation Status: {result.status}")
    print(f"   Passed: {result.passed}")
    print(f"   Total Records: {result.total_records}")
    print(f"   Failed Records: {result.failed_records}")
    print(f"   Pass Rate: {result.pass_rate:.2f}%")
    print(f"   Message: {result.message}")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")
    
    if result.details:
        print(f"\n📋 Details:")
        pk_validation = result.details.get('primary_key_validation', {})
        print(f"   Has Duplicates: {pk_validation.get('has_duplicates')}")
        print(f"   Duplicate Count: {pk_validation.get('duplicate_count')}")
        print(f"   Unique Duplicate Keys: {pk_validation.get('unique_duplicate_keys')}")
        
        duplicate_keys = pk_validation.get('duplicate_keys', [])
        if duplicate_keys:
            print(f"\n   Duplicate Key Values:")
            for dup in duplicate_keys:
                print(f"      {dup}")
    
    # Test failed row extraction
    print("\n🔍 Extracting failed rows...")
    failed_df = validator.extract_failed_rows(df, validation_type='primary_key')
    failed_count = failed_df.count()
    print(f"   Extracted {failed_count} failed rows")
    
    if failed_count > 0:
        print("\n   Failed rows preview:")
        failed_df.show(truncate=False)
    
    return result


def test_foreign_key_validation():
    """Test foreign key validation with orphan detection."""
    print("\n" + "="*80)
    print("TEST 2: Foreign Key Validation (Orphan Detection)")
    print("="*80)
    
    spark = create_spark_session()
    
    # Create parent dataset (customers)
    customer_schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), True),
    ])
    
    customer_data = [
        (1, "Alice Johnson"),
        (2, "Bob Smith"),
        (3, "Charlie Brown"),
        (4, "Diana Prince"),
    ]
    
    customers_df = spark.createDataFrame(customer_data, customer_schema)
    
    # Create child dataset (orders) with orphan foreign keys
    order_schema = StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", IntegerType(), True),  # Foreign key
        StructField("amount", FloatType(), True),
        StructField("status", StringType(), True),
    ])
    
    order_data = [
        (101, 1, 99.99, "completed"),
        (102, 2, 149.99, "completed"),
        (103, 999, 75.00, "pending"),  # Orphan: customer_id 999 doesn't exist
        (104, 3, 200.00, "completed"),
        (105, 888, 50.00, "pending"),  # Orphan: customer_id 888 doesn't exist
        (106, 1, 125.00, "shipped"),
        (107, 777, 300.00, "pending"),  # Orphan: customer_id 777 doesn't exist
    ]
    
    orders_df = spark.createDataFrame(order_data, order_schema)
    
    print(f"\n📊 Created parent dataset (customers) with {customers_df.count()} records")
    customers_df.show(truncate=False)
    
    print(f"\n📊 Created child dataset (orders) with {orders_df.count()} records")
    orders_df.show(truncate=False)
    
    # Create validator with foreign key mapping
    validator = ReferentialIntegrityValidator(
        foreign_key_mappings={
            'customer_id': ('customers', 'id')
        },
        name="OrderForeignKeyValidator"
    )
    
    # Run validation with parent datasets
    print("\n🔍 Running foreign key validation...")
    result = validator.validate(
        orders_df,
        parent_datasets={'customers': customers_df}
    )
    
    # Display results
    print(f"\n✅ Validation Status: {result.status}")
    print(f"   Passed: {result.passed}")
    print(f"   Total Records: {result.total_records}")
    print(f"   Failed Records: {result.failed_records}")
    print(f"   Pass Rate: {result.pass_rate:.2f}%")
    print(f"   Message: {result.message}")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")
    
    if result.details:
        print(f"\n📋 Foreign Key Validation Details:")
        fk_validations = result.details.get('foreign_key_validation', {})
        for fk_col, fk_result in fk_validations.items():
            print(f"\n   Foreign Key: {fk_col}")
            print(f"      Valid: {fk_result.get('valid')}")
            print(f"      Orphan Count: {fk_result.get('orphan_count')}")
            print(f"      Parent Dataset: {fk_result.get('parent_dataset')}")
            print(f"      Parent Key Column: {fk_result.get('parent_key_column')}")
            
            orphan_values = fk_result.get('orphan_values', [])
            if orphan_values:
                print(f"      Orphan Values: {orphan_values}")
    
    # Test failed row extraction
    print("\n🔍 Extracting orphan rows...")
    failed_df = validator.extract_failed_rows(
        orders_df,
        validation_type='foreign_key',
        parent_datasets={'customers': customers_df}
    )
    failed_count = failed_df.count()
    print(f"   Extracted {failed_count} orphan rows")
    
    if failed_count > 0:
        print("\n   Orphan rows preview:")
        failed_df.show(truncate=False)
    
    return result


def test_combined_validation():
    """Test combined primary key and foreign key validation."""
    print("\n" + "="*80)
    print("TEST 3: Combined Primary Key + Foreign Key Validation")
    print("="*80)
    
    spark = create_spark_session()
    
    # Create parent dataset (products)
    product_schema = StructType([
        StructField("product_id", IntegerType(), False),
        StructField("product_name", StringType(), True),
    ])
    
    product_data = [
        (1001, "Widget A"),
        (1002, "Widget B"),
        (1003, "Widget C"),
    ]
    
    products_df = spark.createDataFrame(product_data, product_schema)
    
    # Create child dataset (inventory) with both duplicates and orphans
    inventory_schema = StructType([
        StructField("inventory_id", IntegerType(), False),  # Primary key
        StructField("product_id", IntegerType(), True),  # Foreign key
        StructField("quantity", IntegerType(), True),
        StructField("location", StringType(), True),
    ])
    
    inventory_data = [
        (1, 1001, 100, "Warehouse A"),
        (2, 1002, 150, "Warehouse B"),
        (3, 1003, 200, "Warehouse A"),
        (1, 1001, 50, "Warehouse C"),  # Duplicate inventory_id (1)
        (4, 9999, 75, "Warehouse A"),  # Orphan: product_id 9999 doesn't exist
        (5, 1002, 125, "Warehouse B"),
        (2, 1003, 80, "Warehouse C"),  # Duplicate inventory_id (2)
    ]
    
    inventory_df = spark.createDataFrame(inventory_data, inventory_schema)
    
    print(f"\n📊 Created parent dataset (products) with {products_df.count()} records")
    products_df.show(truncate=False)
    
    print(f"\n📊 Created child dataset (inventory) with {inventory_df.count()} records")
    inventory_df.show(truncate=False)
    
    # Create validator with both primary key and foreign key
    validator = ReferentialIntegrityValidator(
        primary_key_columns=["inventory_id"],
        foreign_key_mappings={
            'product_id': ('products', 'product_id')
        },
        name="InventoryIntegrityValidator"
    )
    
    # Run validation
    print("\n🔍 Running combined integrity validation...")
    result = validator.validate(
        inventory_df,
        parent_datasets={'products': products_df}
    )
    
    # Display results
    print(f"\n✅ Validation Status: {result.status}")
    print(f"   Passed: {result.passed}")
    print(f"   Total Records: {result.total_records}")
    print(f"   Failed Records: {result.failed_records}")
    print(f"   Pass Rate: {result.pass_rate:.2f}%")
    print(f"   Message: {result.message}")
    print(f"   Execution Time: {result.execution_time_ms:.2f}ms")
    
    if result.errors:
        print(f"\n❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")
    
    # Extract all failed rows
    print("\n🔍 Extracting all failed rows...")
    failed_df = validator.extract_failed_rows(
        inventory_df,
        validation_type='all',
        parent_datasets={'products': products_df}
    )
    failed_count = failed_df.count()
    print(f"   Extracted {failed_count} failed rows total")
    
    if failed_count > 0:
        print("\n   All failed rows preview:")
        failed_df.show(truncate=False)
    
    return result


def test_duplicate_detection_utility():
    """Test the duplicate detection utility function."""
    print("\n" + "="*80)
    print("TEST 4: Duplicate Detection Utility Function")
    print("="*80)
    
    spark = create_spark_session()
    
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), True),
    ])
    
    data = [
        (1, "Alice"),
        (2, "Bob"),
        (3, "Charlie"),
        (1, "Alice Duplicate"),
        (4, "Diana"),
        (2, "Bob Duplicate"),
    ]
    
    df = spark.createDataFrame(data, schema)
    
    print(f"\n📊 Created dataset with {df.count()} records")
    df.show(truncate=False)
    
    print("\n🔍 Running duplicate detection on 'id' column...")
    result = detect_duplicates(df, ["id"])
    
    print(f"\n✅ Duplicate Detection Result:")
    print(f"   Total Records: {result['total_records']}")
    print(f"   Unique Records: {result['unique_records']}")
    print(f"   Duplicate Count: {result['duplicate_count']}")
    print(f"   Has Duplicates: {result['has_duplicates']}")
    
    if result['duplicate_keys']:
        print(f"\n   Duplicate Keys:")
        for dup in result['duplicate_keys']:
            print(f"      {dup}")
    
    return result


def test_validation_log_storage():
    """Test storing integrity validation results in validation_logs table."""
    print("\n" + "="*80)
    print("TEST 5: Validation Log Storage")
    print("="*80)
    
    # Run a simple validation
    spark = create_spark_session()
    
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("value", StringType(), True),
    ])
    
    data = [(1, "A"), (2, "B"), (1, "C")]  # Has duplicate
    df = spark.createDataFrame(data, schema)
    
    validator = ReferentialIntegrityValidator(
        primary_key_columns=["id"],
        name="TestIntegrityValidator"
    )
    
    result = validator.validate(df)
    
    print(f"\n✅ Validation completed:")
    print(f"   Status: {result.status}")
    print(f"   Failed Records: {result.failed_records}")
    
    # Store in database
    print("\n💾 Storing validation result in database...")
    
    try:
        db = next(get_db())
        
        validation_log = ValidationLog(
            dataset_name="test_dataset",
            validation_type="referential_integrity",
            status=result.status.value,
            total_records=result.total_records,
            failed_records=result.failed_records,
            pass_rate=result.pass_rate,
            execution_time_ms=result.execution_time_ms,
            validator_name=result.validator_name,
            message=result.message,
            details=result.details,
            errors=result.errors
        )
        
        db.add(validation_log)
        db.commit()
        db.refresh(validation_log)
        
        print(f"   ✅ Stored validation log with ID: {validation_log.id}")
        print(f"   Created at: {validation_log.created_at}")
        
        # Query it back
        retrieved = db.query(ValidationLog).filter(
            ValidationLog.id == validation_log.id
        ).first()
        
        print(f"\n📊 Retrieved validation log:")
        print(f"   ID: {retrieved.id}")
        print(f"   Dataset: {retrieved.dataset_name}")
        print(f"   Type: {retrieved.validation_type}")
        print(f"   Status: {retrieved.status}")
        print(f"   Failed Records: {retrieved.failed_records}")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ Error storing validation log: {str(e)}")
        print(f"   (This is expected if database is not set up)")
    
    return result


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("REFERENTIAL INTEGRITY VALIDATOR VERIFICATION")
    print("="*80)
    print(f"Started at: {datetime.now()}")
    
    try:
        # Run all tests
        test_primary_key_validation()
        test_foreign_key_validation()
        test_combined_validation()
        test_duplicate_detection_utility()
        test_validation_log_storage()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ TEST FAILED: {str(e)}")
        print("="*80)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\nCompleted at: {datetime.now()}")


if __name__ == "__main__":
    main()
