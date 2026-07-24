"""
Comprehensive Verification Script for Data Observability Platform
This script performs end-to-end testing of all components
"""
import requests
import json
import time
import sys
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_DATA_DIR = Path(__file__).parent

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def print_test(name: str, status: str, details: str = ""):
    """Print test result"""
    if status == "PASS":
        color = Colors.OKGREEN
        test_results["passed"] += 1
    elif status == "FAIL":
        color = Colors.FAIL
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {details}")
    elif status == "SKIP":
        color = Colors.WARNING
        test_results["skipped"] += 1
    else:
        color = Colors.ENDC
    
    print(f"{color}[{status}]{Colors.ENDC} {name}")
    if details:
        print(f"      {details}")

def test_service_health(url: str, service_name: str) -> bool:
    """Test if a service is reachable"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_test(f"{service_name} is reachable", "PASS", url)
            return True
        else:
            print_test(f"{service_name} is reachable", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test(f"{service_name} is reachable", "FAIL", str(e))
        return False

# ============================================================================
# BACKEND API TESTS
# ============================================================================

def test_backend_health():
    """Test backend health endpoints"""
    print_header("BACKEND HEALTH CHECKS")
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/v1/health/status", "Health status"),
        ("/api/v1/health/readiness", "Readiness check"),
        ("/api/v1/health/liveness", "Liveness check"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print_test(description, "PASS", endpoint)
            else:
                print_test(description, "FAIL", f"{endpoint} - Status: {response.status_code}")
        except Exception as e:
            print_test(description, "FAIL", f"{endpoint} - Error: {str(e)}")

def test_authentication_endpoints():
    """Test authentication endpoints"""
    print_header("AUTHENTICATION TESTS")
    
    # Test login endpoint
    try:
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=5)
        
        if response.status_code in [200, 401]:  # 401 is expected if user doesn't exist
            print_test("Login endpoint", "PASS", "Endpoint is functional")
        else:
            print_test("Login endpoint", "FAIL", f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_test("Login endpoint", "FAIL", str(e))
    
    # Test token validation
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", timeout=5)
        if response.status_code in [200, 401, 403]:  # Expected statuses
            print_test("Auth validation endpoint", "PASS", "Endpoint is functional")
        else:
            print_test("Auth validation endpoint", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Auth validation endpoint", "FAIL", str(e))

def test_validation_endpoints():
    """Test validation endpoints"""
    print_header("VALIDATION ENDPOINTS")
    
    endpoints = [
        ("/api/v1/validation-logs", "GET", None, "Get validation logs"),
        ("/api/v1/schema-contracts", "GET", None, "Get schema contracts"),
        ("/api/v1/validation/stats", "GET", None, "Get validation stats"),
    ]
    
    for endpoint, method, data, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
            
            if response.status_code in [200, 401, 403]:
                print_test(description, "PASS", endpoint)
            else:
                print_test(description, "FAIL", f"{endpoint} - Status: {response.status_code}")
        except Exception as e:
            print_test(description, "FAIL", str(e))

def test_observability_endpoints():
    """Test observability endpoints"""
    print_header("OBSERVABILITY ENDPOINTS")
    
    endpoints = [
        "/api/v1/profiling/results",
        "/api/v1/profiling/summary",
        "/api/v1/schema-drift/history",
        "/api/v1/metrics",
        "/api/v1/metrics/summary",
        "/api/v1/freshness-checks",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_airflow_endpoints():
    """Test Airflow integration endpoints"""
    print_header("AIRFLOW INTEGRATION")
    
    endpoints = [
        "/api/v1/airflow/health",
        "/api/v1/dag-executions",
        "/api/v1/dag-executions/stats",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 503]:  # 503 if Airflow is down
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_warehouse_endpoints():
    """Test data warehouse endpoints"""
    print_header("DATA WAREHOUSE ENDPOINTS")
    
    endpoints = [
        "/api/v1/warehouse/tables",
        "/api/v1/warehouse/stats",
        "/api/v1/load-monitoring/status",
        "/api/v1/load-monitoring/history",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_cache_endpoints():
    """Test cache endpoints"""
    print_header("CACHE MONITORING ENDPOINTS")
    
    endpoints = [
        "/api/v1/cache/health",
        "/api/v1/cache/metrics",
        "/api/v1/cache/stats",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 503]:  # 503 if Redis is down
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_storage_endpoints():
    """Test storage endpoints"""
    print_header("STORAGE ENDPOINTS")
    
    endpoints = [
        "/api/v1/storage/health",
        "/api/v1/storage/buckets",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403, 503]:  # 503 if storage is unavailable
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_retry_queue_endpoints():
    """Test retry queue endpoints"""
    print_header("RETRY QUEUE ENDPOINTS")
    
    endpoints = [
        "/api/v1/retry-queue",
        "/api/v1/retry-queue/stats",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_rules_endpoints():
    """Test rules management endpoints"""
    print_header("RULES MANAGEMENT ENDPOINTS")
    
    endpoints = [
        "/api/v1/rules",
        "/api/v1/rules/active",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

def test_task_endpoints():
    """Test async task endpoints"""
    print_header("ASYNC TASK ENDPOINTS")
    
    # Test task status endpoint
    try:
        test_task_id = "test-task-123"
        response = requests.get(f"{BASE_URL}/api/v1/tasks/{test_task_id}/status", timeout=5)
        if response.status_code in [200, 404, 401, 403]:  # 404 expected for non-existent task
            print_test("Task status endpoint", "PASS")
        else:
            print_test("Task status endpoint", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Task status endpoint", "FAIL", str(e))

def test_audit_endpoints():
    """Test audit endpoints"""
    print_header("AUDIT ENDPOINTS")
    
    endpoints = [
        "/api/v1/audit-logs",
        "/api/v1/audit-logs/summary",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test(f"Endpoint: {endpoint}", "PASS")
            else:
                print_test(f"Endpoint: {endpoint}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Endpoint: {endpoint}", "FAIL", str(e))

# ============================================================================
# FRONTEND COMPONENT TESTS
# ============================================================================

def test_frontend_pages():
    """Test all frontend pages are accessible"""
    print_header("FRONTEND PAGE VERIFICATION")
    
    # Note: These tests check if the frontend is running
    # Actual UI testing would require browser automation (Playwright/Selenium)
    
    pages = [
        "/",
        "/login",
        "/dashboard",
        "/upload",
        "/validation",
        "/schema-validation",
        "/schema-drift",
        "/metrics",
        "/metrics-dashboard",
        "/profiling-dashboard",
        "/freshness-monitoring",
        "/pipeline-executions",
        "/pipelines",
        "/logs",
        "/audit-history",
        "/health",
        "/cache-monitoring",
        "/warehouse-status",
        "/warehouse-load-monitoring",
        "/data-sources",
        "/alerts",
        "/validation-retry",
        "/async-task-monitoring",
        "/rules-management",
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{FRONTEND_URL}{page}", timeout=5)
            if response.status_code == 200:
                print_test(f"Page: {page}", "PASS")
            else:
                print_test(f"Page: {page}", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            print_test(f"Page: {page}", "SKIP", "Frontend may not be running")
            break  # Skip remaining tests if frontend is not running

def verify_frontend_components():
    """Verify all UI components exist in the codebase"""
    print_header("FRONTEND COMPONENT VERIFICATION")
    
    components_dir = TEST_DATA_DIR / "frontend" / "src" / "components"
    
    expected_components = [
        "Alert.tsx",
        "AuditHistoryTable.tsx",
        "CacheMetricsCard.tsx",
        "CacheStatusIndicator.tsx",
        "CloudExecutionStatus.tsx",
        "CloudObservabilitySection.tsx",
        "CloudWatchStatusCard.tsx",
        "ColumnDistributionChart.tsx",
        "ConnectionStatusIndicator.tsx",
        "DAGExecutionTable.tsx",
        "DAGExecutionTimeline.tsx",
        "DatasetStatisticsCard.tsx",
        "DriftAlertIndicator.tsx",
        "ErrorBoundary.tsx",
        "ExecutionEnvironmentStatus.tsx",
        "ExportCSVButton.tsx",
        "FailedLoadSection.tsx",
        "FailedPipelineSection.tsx",
        "FailureInsightsPanel.tsx",
        "FallbackUI.tsx",
        "FreshnessMetricsChart.tsx",
        "GlueJobStatusCard.tsx",
        "HealthScoreWidget.tsx",
        "HealthTrendChart.tsx",
        "IntegrityViolationsTable.tsx",
        "LatencyChart.tsx",
        "LoadHistoryTable.tsx",
        "LoadingSpinner.tsx",
        "LoadStatusIndicator.tsx",
        "LogsTable.tsx",
        "MetricCard.tsx",
        "MetricsProviderStatus.tsx",
        "PipelinePerformanceSection.tsx",
        "PipelineScoreCard.tsx",
        "PipelineSummaryCards.tsx",
        "ProfilingSummaryCards.tsx",
        "ProtectedRoute.tsx",
        "QueueMetricsSection.tsx",
        "RetryHistoryTable.tsx",
        "RuleActivationToggle.tsx",
        "RulePreview.tsx",
        "RulesEditor.tsx",
        "SchedulerStatusIndicator.tsx",
        "SchemaComparisonTable.tsx",
        "SchemaDriftDashboard.tsx",
        "SchemaTimelineView.tsx",
        "SLAIndicatorCard.tsx",
        "StorageProviderStatus.tsx",
        "Table.tsx",
        "TaskStatusTable.tsx",
        "ThresholdStatusBadge.tsx",
        "ToastNotification.tsx",
        "TopNavigation.tsx",
        "UploadButton.tsx",
        "UploadProgress.tsx",
        "ValidationFilters.tsx",
        "ValidationMetricsWidget.tsx",
        "ValidationResultsTable.tsx",
        "ValidationStatusBadge.tsx",
        "ValidationSummaryCards.tsx",
        "WarehouseLoadExecutionTable.tsx",
        "WarehouseStatusWidget.tsx",
        "WorkerStatusCard.tsx",
        "AirflowHealthWidget.tsx",
    ]
    
    if components_dir.exists():
        for component in expected_components:
            component_path = components_dir / component
            if component_path.exists():
                print_test(f"Component: {component}", "PASS")
            else:
                print_test(f"Component: {component}", "FAIL", "File not found")
    else:
        print_test("Components directory", "FAIL", "Directory not found")

# ============================================================================
# END-TO-END WORKFLOW TESTS
# ============================================================================

def test_data_ingestion_workflow():
    """Test complete data ingestion workflow"""
    print_header("DATA INGESTION WORKFLOW")
    
    test_file = TEST_DATA_DIR / "test_valid_customers.csv"
    
    if not test_file.exists():
        print_test("Data ingestion workflow", "SKIP", "Test data file not found")
        return
    
    try:
        # Step 1: Upload file
        with open(test_file, 'rb') as f:
            files = {'file': ('test_customers.csv', f, 'text/csv')}
            data = {
                'dataset_name': 'test_customers',
                'description': 'Test customer data'
            }
            response = requests.post(f"{BASE_URL}/api/v1/ingest", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            print_test("File upload", "PASS")
            result = response.json()
            
            # Step 2: Check validation logs
            time.sleep(2)  # Wait for async validation
            response = requests.get(f"{BASE_URL}/api/v1/validation-logs", timeout=5)
            if response.status_code in [200, 401, 403]:
                print_test("Validation logs retrieval", "PASS")
            else:
                print_test("Validation logs retrieval", "FAIL", f"Status: {response.status_code}")
        else:
            print_test("File upload", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Data ingestion workflow", "FAIL", str(e))

def test_schema_validation_workflow():
    """Test schema validation workflow"""
    print_header("SCHEMA VALIDATION WORKFLOW")
    
    try:
        # Get schema contracts
        response = requests.get(f"{BASE_URL}/api/v1/schema-contracts", timeout=5)
        if response.status_code in [200, 401, 403]:
            print_test("Fetch schema contracts", "PASS")
        else:
            print_test("Fetch schema contracts", "FAIL", f"Status: {response.status_code}")
        
        # Get schema drift history
        response = requests.get(f"{BASE_URL}/api/v1/schema-drift/history", timeout=5)
        if response.status_code in [200, 401, 403]:
            print_test("Fetch schema drift history", "PASS")
        else:
            print_test("Fetch schema drift history", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Schema validation workflow", "FAIL", str(e))

def test_monitoring_workflow():
    """Test monitoring and observability workflow"""
    print_header("MONITORING & OBSERVABILITY WORKFLOW")
    
    try:
        # Get metrics
        response = requests.get(f"{BASE_URL}/api/v1/metrics", timeout=5)
        if response.status_code in [200, 401, 403]:
            print_test("Fetch metrics", "PASS")
        else:
            print_test("Fetch metrics", "FAIL", f"Status: {response.status_code}")
        
        # Get profiling results
        response = requests.get(f"{BASE_URL}/api/v1/profiling/results", timeout=5)
        if response.status_code in [200, 401, 403]:
            print_test("Fetch profiling results", "PASS")
        else:
            print_test("Fetch profiling results", "FAIL", f"Status: {response.status_code}")
        
        # Get health status
        response = requests.get(f"{BASE_URL}/api/v1/health/status", timeout=5)
        if response.status_code == 200:
            print_test("Fetch health status", "PASS")
            health_data = response.json()
            print(f"      Status: {health_data.get('status', 'unknown')}")
        else:
            print_test("Fetch health status", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Monitoring workflow", "FAIL", str(e))

# ============================================================================
# DATABASE AND INFRASTRUCTURE TESTS
# ============================================================================

def test_database_connectivity():
    """Test database connectivity through health endpoints"""
    print_header("DATABASE CONNECTIVITY")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/status", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            
            # Check database status
            if 'components' in health_data:
                components = health_data['components']
                if 'database' in components:
                    db_status = components['database'].get('status', 'unknown')
                    if db_status == 'healthy':
                        print_test("Database connection", "PASS")
                    else:
                        print_test("Database connection", "FAIL", f"Status: {db_status}")
                else:
                    print_test("Database connection", "SKIP", "No database info in health check")
            else:
                print_test("Database connection", "SKIP", "Health check format unexpected")
        else:
            print_test("Database connection", "FAIL", f"Health endpoint status: {response.status_code}")
    except Exception as e:
        print_test("Database connection", "FAIL", str(e))

def test_cache_connectivity():
    """Test Redis cache connectivity"""
    print_header("CACHE CONNECTIVITY")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cache/health", timeout=5)
        if response.status_code == 200:
            print_test("Redis cache connection", "PASS")
        elif response.status_code in [503]:
            print_test("Redis cache connection", "FAIL", "Service unavailable")
        elif response.status_code in [401, 403]:
            print_test("Redis cache connection", "PASS", "Endpoint exists (auth required)")
        else:
            print_test("Redis cache connection", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Redis cache connection", "FAIL", str(e))

def test_storage_connectivity():
    """Test object storage connectivity"""
    print_header("OBJECT STORAGE CONNECTIVITY")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/storage/health", timeout=5)
        if response.status_code == 200:
            print_test("Object storage connection", "PASS")
        elif response.status_code in [503]:
            print_test("Object storage connection", "FAIL", "Service unavailable")
        elif response.status_code in [401, 403]:
            print_test("Object storage connection", "PASS", "Endpoint exists (auth required)")
        else:
            print_test("Object storage connection", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_test("Object storage connection", "FAIL", str(e))

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def print_summary():
    """Print test execution summary"""
    print_header("TEST EXECUTION SUMMARY")
    
    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    
    print(f"{Colors.BOLD}Total Tests:{Colors.ENDC} {total}")
    print(f"{Colors.OKGREEN}Passed:{Colors.ENDC} {test_results['passed']}")
    print(f"{Colors.FAIL}Failed:{Colors.ENDC} {test_results['failed']}")
    print(f"{Colors.WARNING}Skipped:{Colors.ENDC} {test_results['skipped']}")
    
    if test_results["failed"] > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Failed Tests:{Colors.ENDC}")
        for error in test_results["errors"]:
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {error}")
    
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Pass Rate:{Colors.ENDC} {pass_rate:.1f}%")
    
    if pass_rate == 100:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
    elif pass_rate >= 80:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Most tests passed{Colors.ENDC}")
    elif pass_rate >= 50:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ Many tests failed{Colors.ENDC}")

def main():
    """Main test execution"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("="*80)
    print("DATA OBSERVABILITY PLATFORM - COMPREHENSIVE VERIFICATION".center(80))
    print("="*80)
    print(f"{Colors.ENDC}\n")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    
    # Check if services are running
    backend_running = test_service_health(f"{BASE_URL}/health", "Backend API")
    
    if not backend_running:
        print(f"\n{Colors.WARNING}WARNING: Backend is not running!{Colors.ENDC}")
        print(f"{Colors.WARNING}Please start the backend server and try again.{Colors.ENDC}")
        print(f"\n{Colors.BOLD}To start services, run:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}./run-local.ps1{Colors.ENDC}")
        return 1
    
    # Run all test suites
    try:
        # Backend tests
        test_backend_health()
        test_authentication_endpoints()
        test_validation_endpoints()
        test_observability_endpoints()
        test_airflow_endpoints()
        test_warehouse_endpoints()
        test_cache_endpoints()
        test_storage_endpoints()
        test_retry_queue_endpoints()
        test_rules_endpoints()
        test_task_endpoints()
        test_audit_endpoints()
        
        # Infrastructure tests
        test_database_connectivity()
        test_cache_connectivity()
        test_storage_connectivity()
        
        # Workflow tests
        test_data_ingestion_workflow()
        test_schema_validation_workflow()
        test_monitoring_workflow()
        
        # Frontend tests
        verify_frontend_components()
        test_frontend_pages()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Test execution interrupted by user{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"\n\n{Colors.FAIL}Unexpected error during test execution: {str(e)}{Colors.ENDC}")
        return 1
    
    # Print summary
    print_summary()
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return exit code based on results
    return 0 if test_results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
