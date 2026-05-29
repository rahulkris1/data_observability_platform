"""Test script to verify schema contract validation

This script demonstrates:
1. Loading schema contracts from JSON files
2. Validating datasets against contracts
3. Detecting schema mismatches
"""
from app.services.schema_contract_service import get_schema_contract_service


def test_customer_schema_valid():
    """Test validation with a valid customer dataset"""
    print("\n" + "="*80)
    print("TEST 1: Valid Customer Dataset")
    print("="*80)
    
    service = get_schema_contract_service()
    
    # Simulate a valid customer dataset
    dataset_columns = [
        {"name": "customer_id", "data_type": "integer"},
        {"name": "first_name", "data_type": "string"},
        {"name": "last_name", "data_type": "string"},
        {"name": "email", "data_type": "string"},
        {"name": "phone", "data_type": "string"},
        {"name": "date_of_birth", "data_type": "date"},
        {"name": "registration_date", "data_type": "timestamp"},
        {"name": "is_active", "data_type": "boolean"},
        {"name": "loyalty_points", "data_type": "integer"},
        {"name": "account_balance", "data_type": "float"},
    ]
    
    result = service.validate_dataset("customer_schema", dataset_columns)
    
    print(f"Contract: {result.contract_name}")
    print(f"Dataset: {result.dataset_name}")
    print(f"Valid: {result.is_valid}")
    print(f"Expected Columns: {result.total_columns_expected}")
    print(f"Actual Columns: {result.total_columns_actual}")
    print(f"Errors: {len(result.errors)}")
    
    if result.errors:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"  - {error.message}")
    else:
        print("\n✅ Validation PASSED!")


def test_customer_schema_missing_columns():
    """Test validation with missing required columns"""
    print("\n" + "="*80)
    print("TEST 2: Customer Dataset with Missing Required Columns")
    print("="*80)
    
    service = get_schema_contract_service()
    
    # Missing required columns: email, registration_date, is_active
    dataset_columns = [
        {"name": "customer_id", "data_type": "integer"},
        {"name": "first_name", "data_type": "string"},
        {"name": "last_name", "data_type": "string"},
        {"name": "phone", "data_type": "string"},
    ]
    
    result = service.validate_dataset("customer_schema", dataset_columns)
    
    print(f"Contract: {result.contract_name}")
    print(f"Dataset: {result.dataset_name}")
    print(f"Valid: {result.is_valid}")
    print(f"Expected Columns: {result.total_columns_expected}")
    print(f"Actual Columns: {result.total_columns_actual}")
    print(f"Errors: {len(result.errors)}")
    
    if result.errors:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"  - [{error.error_type}] {error.message}")
    else:
        print("\n✅ Validation PASSED!")


def test_customer_schema_type_mismatch():
    """Test validation with incorrect data types"""
    print("\n" + "="*80)
    print("TEST 3: Customer Dataset with Type Mismatches")
    print("="*80)
    
    service = get_schema_contract_service()
    
    # Wrong data types: customer_id should be integer, not string
    # is_active should be boolean, not string
    dataset_columns = [
        {"name": "customer_id", "data_type": "string"},  # ❌ Should be integer
        {"name": "first_name", "data_type": "string"},
        {"name": "last_name", "data_type": "string"},
        {"name": "email", "data_type": "string"},
        {"name": "phone", "data_type": "string"},
        {"name": "date_of_birth", "data_type": "date"},
        {"name": "registration_date", "data_type": "timestamp"},
        {"name": "is_active", "data_type": "string"},  # ❌ Should be boolean
        {"name": "loyalty_points", "data_type": "integer"},
        {"name": "account_balance", "data_type": "float"},
    ]
    
    result = service.validate_dataset("customer_schema", dataset_columns)
    
    print(f"Contract: {result.contract_name}")
    print(f"Dataset: {result.dataset_name}")
    print(f"Valid: {result.is_valid}")
    print(f"Expected Columns: {result.total_columns_expected}")
    print(f"Actual Columns: {result.total_columns_actual}")
    print(f"Errors: {len(result.errors)}")
    
    if result.errors:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"  - [{error.error_type}] {error.message}")
            if error.column_name:
                print(f"    Column: {error.column_name}")
                print(f"    Expected: {error.expected}, Actual: {error.actual}")
    else:
        print("\n✅ Validation PASSED!")


def test_orders_schema_extra_columns():
    """Test validation with unexpected extra columns"""
    print("\n" + "="*80)
    print("TEST 4: Orders Dataset with Extra Columns")
    print("="*80)
    
    service = get_schema_contract_service()
    
    # All required columns plus extra columns not in contract
    dataset_columns = [
        {"name": "order_id", "data_type": "integer"},
        {"name": "customer_id", "data_type": "integer"},
        {"name": "order_date", "data_type": "timestamp"},
        {"name": "total_amount", "data_type": "float"},
        {"name": "currency", "data_type": "string"},
        {"name": "status", "data_type": "string"},
        {"name": "shipping_address", "data_type": "string"},
        {"name": "tax_amount", "data_type": "float"},
        {"name": "payment_method", "data_type": "string"},
        {"name": "extra_field_1", "data_type": "string"},  # ❌ Not in contract
        {"name": "extra_field_2", "data_type": "integer"},  # ❌ Not in contract
    ]
    
    result = service.validate_dataset("orders_schema", dataset_columns)
    
    print(f"Contract: {result.contract_name}")
    print(f"Dataset: {result.dataset_name}")
    print(f"Valid: {result.is_valid}")
    print(f"Expected Columns: {result.total_columns_expected}")
    print(f"Actual Columns: {result.total_columns_actual}")
    print(f"Errors: {len(result.errors)}")
    
    if result.errors:
        print("\nValidation Errors:")
        for error in result.errors:
            print(f"  - [{error.error_type}] {error.message}")
    else:
        print("\n✅ Validation PASSED!")


def test_validation_summary():
    """Test validation summary statistics"""
    print("\n" + "="*80)
    print("TEST 5: Validation Summary Statistics")
    print("="*80)
    
    service = get_schema_contract_service()
    summary = service.get_validation_summary()
    
    print(f"Total Validations: {summary.total_validations}")
    print(f"Passed: {summary.passed}")
    print(f"Failed: {summary.failed}")
    print(f"Success Rate: {summary.success_rate}%")


def test_list_contracts():
    """Test listing all loaded contracts"""
    print("\n" + "="*80)
    print("TEST 6: List All Contracts")
    print("="*80)
    
    service = get_schema_contract_service()
    contracts = service.get_all_contracts()
    
    print(f"Total Contracts Loaded: {len(contracts)}")
    print("\nContracts:")
    for contract in contracts:
        print(f"\n  Name: {contract.name}")
        print(f"  Dataset: {contract.dataset_name}")
        print(f"  Version: {contract.version}")
        print(f"  Active: {contract.is_active}")
        print(f"  Columns: {len(contract.schema_definition['columns'])}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "Schema Contract Validation Test Suite" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    # Run all tests
    test_list_contracts()
    test_customer_schema_valid()
    test_customer_schema_missing_columns()
    test_customer_schema_type_mismatch()
    test_orders_schema_extra_columns()
    test_validation_summary()
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80 + "\n")
