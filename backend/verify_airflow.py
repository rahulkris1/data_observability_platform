"""
Airflow Health Check and Verification Script
Verifies Airflow scheduler and webserver are running properly
"""
import requests
import time
import sys
from typing import Dict, Tuple


def check_airflow_webserver(base_url: str = "http://localhost:8080") -> Tuple[bool, str]:
    """Check if Airflow webserver is healthy"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            metadatabase = health_data.get("metadatabase", {}).get("status", "")
            scheduler = health_data.get("scheduler", {}).get("status", "")
            
            if metadatabase == "healthy" and scheduler == "healthy":
                return True, f"✓ Webserver healthy (metadatabase: {metadatabase}, scheduler: {scheduler})"
            else:
                return False, f"✗ Webserver unhealthy (metadatabase: {metadatabase}, scheduler: {scheduler})"
        else:
            return False, f"✗ Webserver returned status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Cannot connect to webserver: {str(e)}"


def check_airflow_api(base_url: str = "http://localhost:8080") -> Tuple[bool, str]:
    """Check if Airflow API is accessible"""
    try:
        response = requests.get(
            f"{base_url}/api/v1/version",
            auth=("admin", "admin123"),
            timeout=5
        )
        if response.status_code == 200:
            version_data = response.json()
            version = version_data.get("version", "unknown")
            return True, f"✓ API accessible (Airflow version: {version})"
        else:
            return False, f"✗ API returned status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Cannot connect to API: {str(e)}"


def check_scheduler_status(base_url: str = "http://localhost:8080") -> Tuple[bool, str]:
    """Check scheduler health via API"""
    try:
        response = requests.get(
            f"{base_url}/api/v1/health",
            auth=("admin", "admin123"),
            timeout=5
        )
        if response.status_code == 200:
            health_data = response.json()
            scheduler = health_data.get("scheduler", {})
            status = scheduler.get("status", "")
            latest_heartbeat = scheduler.get("latest_scheduler_heartbeat", "")
            
            if status == "healthy":
                return True, f"✓ Scheduler healthy (last heartbeat: {latest_heartbeat})"
            else:
                return False, f"✗ Scheduler status: {status}"
        else:
            return False, f"✗ Health endpoint returned: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Cannot check scheduler: {str(e)}"


def check_dags_folder(base_url: str = "http://localhost:8080") -> Tuple[bool, str]:
    """Check if DAGs are being loaded"""
    try:
        response = requests.get(
            f"{base_url}/api/v1/dags",
            auth=("admin", "admin123"),
            timeout=5
        )
        if response.status_code == 200:
            dags_data = response.json()
            total_entries = dags_data.get("total_entries", 0)
            return True, f"✓ DAGs folder accessible ({total_entries} DAGs found)"
        else:
            return False, f"✗ DAGs endpoint returned: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"✗ Cannot access DAGs: {str(e)}"


def verify_airflow(wait_time: int = 60, retry_interval: int = 5) -> bool:
    """
    Verify Airflow is fully operational
    
    Args:
        wait_time: Maximum time to wait for Airflow to become ready (seconds)
        retry_interval: Time between retries (seconds)
    
    Returns:
        True if all checks pass, False otherwise
    """
    print("=" * 70)
    print("Airflow Health Verification")
    print("=" * 70)
    
    base_url = "http://localhost:8080"
    start_time = time.time()
    
    checks = [
        ("Webserver Health", check_airflow_webserver),
        ("API Accessibility", check_airflow_api),
        ("Scheduler Status", check_scheduler_status),
        ("DAGs Folder", check_dags_folder),
    ]
    
    # Wait for Airflow to be ready
    print(f"\nWaiting for Airflow to be ready (max {wait_time}s)...")
    while time.time() - start_time < wait_time:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Airflow webserver is responding\n")
                break
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s)", end="\r")
        time.sleep(retry_interval)
    else:
        print(f"\n✗ Airflow did not become ready within {wait_time}s")
        return False
    
    # Run all checks
    print("Running health checks:\n")
    all_passed = True
    results = []
    
    for check_name, check_func in checks:
        passed, message = check_func(base_url)
        results.append((check_name, passed, message))
        print(f"  {check_name}: {message}")
        if not passed:
            all_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    print(f"Checks passed: {passed_count}/{total_count}")
    
    if all_passed:
        print("\n✓ All Airflow components are healthy!")
        print(f"✓ Airflow UI available at: {base_url}")
        print("✓ Login credentials: admin / admin123")
        return True
    else:
        print("\n✗ Some checks failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Allow custom wait time from command line
    wait_time = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    
    success = verify_airflow(wait_time=wait_time)
    sys.exit(0 if success else 1)
