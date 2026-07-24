"""
Backend Component Verification Script
Validates that all backend components exist and contain expected functionality
"""
import os
import re
from pathlib import Path
from typing import List, Dict

# ANSI color codes
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    HEADER = '\033[95m'

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "issues": []
}

def print_header(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def check_file_exists(file_path: Path, file_name: str) -> bool:
    """Check if file exists"""
    if file_path.exists():
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {file_name}")
        results["passed"] += 1
        return True
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC} {file_name} NOT FOUND")
        results["failed"] += 1
        results["issues"].append(f"{file_name} not found")
        return False

def check_file_contains(file_path: Path, file_name: str, expected_elements: List[str]):
    """Check if file contains expected elements"""
    if not file_path.exists():
        return
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        missing_elements = []
        for element in expected_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"{Colors.WARNING}  ⚠ {file_name}: Missing elements: {', '.join(missing_elements)}{Colors.ENDC}")
            results["warnings"] += 1
        else:
            print(f"  {Colors.OKGREEN}✓ {file_name} structure validated{Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}  ✗ Error reading {file_name}: {str(e)}{Colors.ENDC}")
        results["failed"] += 1

def verify_api_routes(backend_dir: Path):
    """Verify all API route files"""
    print_header("API ROUTES VERIFICATION")
    
    api_dir = backend_dir / "app" / "api"
    
    route_files = {
        "airflow_routes.py": ["router", "APIRouter", "airflow"],
        "audit_logs.py": ["router", "APIRouter", "audit"],
        "auth_routes.py": ["router", "APIRouter", "login"],
        "cache_routes.py": ["router", "APIRouter", "cache"],
        "dag_execution_routes.py": ["router", "APIRouter", "dag"],
        "freshness_routes.py": ["router", "APIRouter", "freshness"],
        "glue_routes.py": ["router", "APIRouter", "glue"],
        "health_routes.py": ["router", "APIRouter", "health"],
        "load_monitoring_routes.py": ["router", "APIRouter", "load"],
        "metrics_routes.py": ["router", "APIRouter", "metrics"],
        "observability_routes.py": ["router", "APIRouter"],
        "profiling_routes.py": ["router", "APIRouter", "profiling"],
        "retry_routes.py": ["router", "APIRouter", "retry"],
        "rules_routes.py": ["router", "APIRouter", "rules"],
        "schema_contracts.py": ["router", "APIRouter", "schema"],
        "schema_drift_routes.py": ["router", "APIRouter", "drift"],
        "storage_routes.py": ["router", "APIRouter", "storage"],
        "task_routes.py": ["router", "APIRouter", "task"],
        "validation_routes.py": ["router", "APIRouter", "validation"],
        "warehouse_routes.py": ["router", "APIRouter", "warehouse"],
    }
    
    for route_file, expected in route_files.items():
        route_path = api_dir / route_file
        if check_file_exists(route_path, route_file):
            check_file_contains(route_path, route_file, expected)

def verify_models(backend_dir: Path):
    """Verify database models"""
    print_header("DATABASE MODELS VERIFICATION")
    
    models_dir = backend_dir / "app" / "models"
    
    if not models_dir.exists():
        print(f"{Colors.FAIL}✗ Models directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for model files
    model_files = list(models_dir.glob("*.py"))
    model_files = [f for f in model_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(model_files) == 0:
        print(f"{Colors.FAIL}✗ No model files found{Colors.ENDC}")
        results["failed"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(model_files)} model files{Colors.ENDC}")
        for model_file in model_files:
            print(f"  - {model_file.name}")
            
            # Check if file contains SQLAlchemy models
            try:
                content = model_file.read_text(encoding='utf-8')
                if "Base" in content or "Table" in content or "Column" in content:
                    results["passed"] += 1
                else:
                    print(f"{Colors.WARNING}    ⚠ May not be a valid SQLAlchemy model{Colors.ENDC}")
                    results["warnings"] += 1
            except Exception as e:
                print(f"{Colors.WARNING}    ⚠ Error reading file: {str(e)}{Colors.ENDC}")
                results["warnings"] += 1

def verify_services(backend_dir: Path):
    """Verify service layer"""
    print_header("SERVICE LAYER VERIFICATION")
    
    services_dir = backend_dir / "app" / "services"
    
    if not services_dir.exists():
        print(f"{Colors.FAIL}✗ Services directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for service files
    service_files = list(services_dir.glob("*.py"))
    service_files = [f for f in service_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(service_files) == 0:
        print(f"{Colors.FAIL}✗ No service files found{Colors.ENDC}")
        results["failed"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(service_files)} service files{Colors.ENDC}")
        for service_file in service_files:
            print(f"  - {service_file.name}")
            results["passed"] += 1

def verify_validators(backend_dir: Path):
    """Verify validator implementations"""
    print_header("VALIDATORS VERIFICATION")
    
    validators_dir = backend_dir / "app" / "validators"
    
    if not validators_dir.exists():
        print(f"{Colors.FAIL}✗ Validators directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for validator files
    validator_files = list(validators_dir.glob("*.py"))
    validator_files = [f for f in validator_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(validator_files) == 0:
        print(f"{Colors.FAIL}✗ No validator files found{Colors.ENDC}")
        results["failed"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(validator_files)} validator files{Colors.ENDC}")
        for validator_file in validator_files:
            print(f"  - {validator_file.name}")
            results["passed"] += 1

def verify_database_migrations(backend_dir: Path):
    """Verify Alembic migrations"""
    print_header("DATABASE MIGRATIONS VERIFICATION")
    
    versions_dir = backend_dir / "alembic" / "versions"
    
    if not versions_dir.exists():
        print(f"{Colors.FAIL}✗ Alembic versions directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for migration files
    migration_files = list(versions_dir.glob("*.py"))
    migration_files = [f for f in migration_files if not f.name.startswith("__pycache__")]
    
    if len(migration_files) == 0:
        print(f"{Colors.WARNING}⚠ No migration files found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(migration_files)} migration files{Colors.ENDC}")
        for migration_file in migration_files:
            print(f"  - {migration_file.name}")
            results["passed"] += 1

def verify_config_files(backend_dir: Path):
    """Verify configuration files"""
    print_header("CONFIGURATION FILES VERIFICATION")
    
    config_files = [
        ("requirements.txt", ["fastapi", "sqlalchemy"]),
        ("alembic.ini", ["alembic", "script_location"]),
        ("pytest.ini", ["pytest"]),
    ]
    
    for config_file, expected in config_files:
        config_path = backend_dir / config_file
        if config_path.exists():
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} {config_file} exists")
            results["passed"] += 1
            
            try:
                content = config_path.read_text(encoding='utf-8')
                missing = [e for e in expected if e not in content]
                if missing:
                    print(f"{Colors.WARNING}  ⚠ Missing elements: {', '.join(missing)}{Colors.ENDC}")
                    results["warnings"] += 1
            except Exception as e:
                print(f"{Colors.WARNING}  ⚠ Error reading file: {str(e)}{Colors.ENDC}")
                results["warnings"] += 1
        else:
            print(f"{Colors.FAIL}✗{Colors.ENDC} {config_file} NOT FOUND")
            results["failed"] += 1
            results["issues"].append(f"Config file {config_file} not found")

def verify_observability_components(backend_dir: Path):
    """Verify observability components"""
    print_header("OBSERVABILITY COMPONENTS VERIFICATION")
    
    observability_dir = backend_dir / "app" / "observability"
    
    if not observability_dir.exists():
        print(f"{Colors.FAIL}✗ Observability directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for observability files
    obs_files = list(observability_dir.glob("*.py"))
    obs_files = [f for f in obs_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(obs_files) == 0:
        print(f"{Colors.WARNING}⚠ No observability files found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(obs_files)} observability files{Colors.ENDC}")
        for obs_file in obs_files:
            print(f"  - {obs_file.name}")
            results["passed"] += 1

def verify_warehouse_components(backend_dir: Path):
    """Verify warehouse components"""
    print_header("WAREHOUSE COMPONENTS VERIFICATION")
    
    warehouse_dir = backend_dir / "app" / "warehouse"
    
    if not warehouse_dir.exists():
        print(f"{Colors.FAIL}✗ Warehouse directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for warehouse files
    warehouse_files = list(warehouse_dir.glob("*.py"))
    warehouse_files = [f for f in warehouse_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(warehouse_files) == 0:
        print(f"{Colors.WARNING}⚠ No warehouse files found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(warehouse_files)} warehouse files{Colors.ENDC}")
        for warehouse_file in warehouse_files:
            print(f"  - {warehouse_file.name}")
            results["passed"] += 1

def verify_storage_components(backend_dir: Path):
    """Verify storage components"""
    print_header("STORAGE COMPONENTS VERIFICATION")
    
    storage_dir = backend_dir / "app" / "storage"
    
    if not storage_dir.exists():
        print(f"{Colors.FAIL}✗ Storage directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for storage files
    storage_files = list(storage_dir.glob("*.py"))
    storage_files = [f for f in storage_files if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
    
    if len(storage_files) == 0:
        print(f"{Colors.WARNING}⚠ No storage files found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(storage_files)} storage files{Colors.ENDC}")
        for storage_file in storage_files:
            print(f"  - {storage_file.name}")
            results["passed"] += 1

def verify_test_files(backend_dir: Path):
    """Verify test files"""
    print_header("TEST FILES VERIFICATION")
    
    tests_dir = backend_dir / "tests"
    
    if not tests_dir.exists():
        print(f"{Colors.FAIL}✗ Tests directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check unit tests
    unit_tests_dir = tests_dir / "unit"
    if unit_tests_dir.exists():
        unit_tests = list(unit_tests_dir.glob("test_*.py"))
        print(f"{Colors.OKGREEN}✓ Found {len(unit_tests)} unit tests{Colors.ENDC}")
        for test_file in unit_tests:
            print(f"  - {test_file.name}")
            results["passed"] += 1
    else:
        print(f"{Colors.WARNING}⚠ Unit tests directory not found{Colors.ENDC}")
        results["warnings"] += 1
    
    # Check integration tests
    integration_tests_dir = tests_dir / "integration"
    if integration_tests_dir.exists():
        integration_tests = list(integration_tests_dir.glob("test_*.py"))
        print(f"{Colors.OKGREEN}✓ Found {len(integration_tests)} integration tests{Colors.ENDC}")
        for test_file in integration_tests:
            print(f"  - {test_file.name}")
            results["passed"] += 1
    else:
        print(f"{Colors.WARNING}⚠ Integration tests directory not found{Colors.ENDC}")
        results["warnings"] += 1

def verify_main_app(backend_dir: Path):
    """Verify main application file"""
    print_header("MAIN APPLICATION VERIFICATION")
    
    main_file = backend_dir / "app" / "main.py"
    
    if check_file_exists(main_file, "app/main.py"):
        check_file_contains(main_file, "app/main.py", [
            "FastAPI",
            "CORSMiddleware",
            "include_router",
            "app = FastAPI"
        ])

def print_summary():
    """Print verification summary"""
    print_header("VERIFICATION SUMMARY")
    
    total = results["passed"] + results["failed"] + results["warnings"]
    
    print(f"{Colors.BOLD}Total Checks:{Colors.ENDC} {total}")
    print(f"{Colors.OKGREEN}Passed:{Colors.ENDC} {results['passed']}")
    print(f"{Colors.FAIL}Failed:{Colors.ENDC} {results['failed']}")
    print(f"{Colors.WARNING}Warnings:{Colors.ENDC} {results['warnings']}")
    
    if results["issues"]:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Issues Found:{Colors.ENDC}")
        for issue in results["issues"]:
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {issue}")
    
    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate:{Colors.ENDC} {success_rate:.1f}%")
    
    if results["failed"] == 0 and results["warnings"] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL BACKEND COMPONENTS VERIFIED SUCCESSFULLY!{Colors.ENDC}")
        return 0
    elif results["failed"] == 0:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ All components present with some warnings{Colors.ENDC}")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ Some components are missing or have issues{Colors.ENDC}")
        return 1

def main():
    """Main verification execution"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("="*80)
    print("BACKEND COMPONENTS COMPREHENSIVE VERIFICATION".center(80))
    print("="*80)
    print(f"{Colors.ENDC}\n")
    
    # Get project directory
    project_dir = Path(__file__).parent
    backend_dir = project_dir / "backend"
    
    if not backend_dir.exists():
        print(f"{Colors.FAIL}ERROR: Backend directory not found!{Colors.ENDC}")
        print(f"Expected path: {backend_dir}")
        return 1
    
    print(f"Backend directory: {backend_dir}")
    
    # Run verification suites
    verify_main_app(backend_dir)
    verify_config_files(backend_dir)
    verify_api_routes(backend_dir)
    verify_models(backend_dir)
    verify_services(backend_dir)
    verify_validators(backend_dir)
    verify_observability_components(backend_dir)
    verify_warehouse_components(backend_dir)
    verify_storage_components(backend_dir)
    verify_database_migrations(backend_dir)
    verify_test_files(backend_dir)
    
    # Print summary
    return print_summary()

if __name__ == "__main__":
    import sys
    sys.exit(main())
