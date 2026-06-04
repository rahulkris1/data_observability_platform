"""
Test script for validation API endpoints

This script tests the validation execution and audit history endpoints.
Run this after starting the FastAPI backend server.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_validation_execution():
    """Test the validation execution endpoint"""
    print("\n" + "="*60)
    print("Testing POST /api/v1/validations/execute")
    print("="*60)
    
    # Test payload
    payload = {
        "dataset_name": "customers.csv",
        "null_threshold": 5.0
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/validations/execute",
            json=payload,
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Validation execution successful!")
            print(f"\nDataset: {result['dataset_name']}")
            print(f"Overall status: {result['overall_status']}")
            print(f"Overall passed: {result['overall_passed']}")
            print(f"Total validators: {result['total_validators']}")
            print(f"Passed validators: {result['passed_validators']}")
            print(f"Failed validators: {result['failed_validators']}")
            print(f"Total records: {result['total_records']}")
            print(f"Execution time: {result['total_execution_time_ms']:.2f}ms")
            
            print(f"\nValidator results:")
            for validator in result['validators']:
                status_emoji = "✅" if validator['passed'] else "❌"
                print(f"  {status_emoji} {validator['validator_name']}: {validator['status']} ({validator['pass_rate']:.1f}%)")
            
            return True
        else:
            print(f"\n❌ Validation execution failed!")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error! Is the backend server running?")
        print(f"   Start it with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_audit_history():
    """Test the audit history endpoint"""
    print("\n" + "="*60)
    print("Testing GET /api/v1/audit/history")
    print("="*60)
    
    # Test with various filters
    test_cases = [
        {"name": "All records (limit 10)", "params": {"limit": 10}},
        {"name": "Filter by status", "params": {"status": "passed", "limit": 5}},
        {"name": "Sort ascending", "params": {"sort_order": "asc", "limit": 5}},
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Parameters: {test_case['params']}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/audit/history",
                params=test_case['params'],
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Total count: {result['total_count']}")
                print(f"Returned items: {len(result['items'])}")
                print(f"Limit: {result['limit']}")
                print(f"Offset: {result['offset']}")
                
                if result['items']:
                    print(f"\nFirst item:")
                    item = result['items'][0]
                    print(f"  ID: {item['id']}")
                    print(f"  Dataset: {item['dataset_name']}")
                    print(f"  Type: {item['validation_type']}")
                    print(f"  Status: {item['status']}")
                    print(f"  Pass rate: {item['pass_rate']:.1f}%")
                    print(f"  Created: {item['created_at']}")
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Test 1: Missing required field
    print("\n1. Missing dataset_name:")
    response = requests.post(
        f"{BASE_URL}/validations/execute",
        json={},
        timeout=10
    )
    print(f"   Status: {response.status_code} (expected 422)")
    print(f"   Response: {response.json()}")
    
    # Test 2: Dataset not found
    print("\n2. Dataset not found:")
    response = requests.post(
        f"{BASE_URL}/validations/execute",
        json={"dataset_name": "nonexistent_dataset.csv"},
        timeout=10
    )
    print(f"   Status: {response.status_code} (expected 404)")
    if response.status_code != 200:
        print(f"   Error message: {response.json()['detail']}")


def main():
    """Run all tests"""
    print("="*60)
    print("Validation API Test Suite")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    test_validation_execution()
    test_audit_history()
    test_error_handling()
    
    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()
