"""
Test Data Ingestion and Complete Workflow
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def test_file_upload(file_path, dataset_name, description):
    """Test file upload"""
    print(f"\n[Testing] Upload: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'text/csv')}
            data = {
                'dataset_name': dataset_name,
                'description': description
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/ingest",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  [OK] Upload successful")
                print(f"  Dataset: {dataset_name}")
                if 'data' in result:
                    print(f"  Details: {json.dumps(result['data'], indent=2)}")
                return result
            else:
                print(f"  [FAIL] Status {response.status_code}")
                print(f"  Error: {response.text}")
                return None
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return None

def test_validation(dataset_name):
    """Test validation execution"""
    print(f"\n[Testing] Validation: {dataset_name}")
    
    try:
        payload = {
            "dataset_name": dataset_name,
            "validation_type": "schema"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/validations/execute",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  [OK] Validation executed")
            return result
        else:
            print(f"  [FAIL] Status {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return None

def test_profiling(dataset_name):
    """Test data profiling"""
    print(f"\n[Testing] Profiling: {dataset_name}")
    
    try:
        payload = {
            "dataset_name": dataset_name,
            "include_statistics": True,
            "include_quality_metrics": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/profiling/execute",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  [OK] Profiling executed")
            return result
        else:
            print(f"  [FAIL] Status {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return None

def get_audit_logs():
    """Get recent audit logs"""
    print(f"\n[Testing] Get Audit Logs")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/audit/recent/list",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  [OK] Retrieved audit logs")
            if 'data' in result and isinstance(result['data'], list):
                print(f"  Count: {len(result['data'])} logs")
            return result
        else:
            print(f"  [FAIL] Status {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return None

def main():
    print_section("DATA OBSERVABILITY PLATFORM - WORKFLOW TEST")
    
    # Test datasets
    test_cases = [
        {
            'file': 'test_valid_customers.csv',
            'dataset': 'customers_valid',
            'description': 'Valid customer data with all fields'
        },
        {
            'file': 'test_missing_column.csv',
            'dataset': 'customers_missing_column',
            'description': 'Customer data with missing email column'
        },
        {
            'file': 'test_null_values.csv',
            'dataset': 'customers_nulls',
            'description': 'Customer data with null values'
        },
        {
            'file': 'test_duplicates.csv',
            'dataset': 'customers_duplicates',
            'description': 'Customer data with duplicate IDs'
        }
    ]
    
    results = {
        'uploads': 0,
        'validations': 0,
        'profiling': 0,
        'total_tests': len(test_cases)
    }
    
    # Phase 1: Upload datasets
    print_section("PHASE 1: Data Ingestion")
    uploaded_datasets = []
    
    for test_case in test_cases:
        result = test_file_upload(
            test_case['file'],
            test_case['dataset'],
            test_case['description']
        )
        
        if result:
            results['uploads'] += 1
            uploaded_datasets.append(test_case['dataset'])
        
        time.sleep(1)  # Brief pause between uploads
    
    # Phase 2: Validation
    print_section("PHASE 2: Data Validation")
    for dataset in uploaded_datasets:
        result = test_validation(dataset)
        if result:
            results['validations'] += 1
        time.sleep(1)
    
    # Phase 3: Profiling
    print_section("PHASE 3: Data Profiling")
    for dataset in uploaded_datasets:
        result = test_profiling(dataset)
        if result:
            results['profiling'] += 1
        time.sleep(1)
    
    # Phase 4: Audit Logs
    print_section("PHASE 4: Audit Logging")
    get_audit_logs()
    
    # Summary
    print_section("TEST SUMMARY")
    print(f"Uploads:     {results['uploads']}/{results['total_tests']}")
    print(f"Validations: {results['validations']}/{results['uploads']}")
    print(f"Profiling:   {results['profiling']}/{results['uploads']}")
    
    success_rate = (
        (results['uploads'] + results['validations'] + results['profiling']) /
        (results['total_tests'] * 3)
    ) * 100
    
    print(f"\nOverall Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n[SUCCESS] All tests passed!")
    elif success_rate >= 75:
        print("\n[PARTIAL] Most tests passed, some issues found")
    else:
        print("\n[FAILURE] Multiple tests failed, needs attention")

if __name__ == "__main__":
    main()
