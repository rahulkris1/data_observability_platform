"""
UI Component Verification Script
Validates that all frontend components exist and contain expected functionality
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

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

def check_component_exists(component_path: Path, component_name: str) -> bool:
    """Check if component file exists"""
    if component_path.exists():
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {component_name} exists")
        results["passed"] += 1
        return True
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC} {component_name} NOT FOUND")
        results["failed"] += 1
        results["issues"].append(f"Component {component_name} not found")
        return False

def check_component_structure(component_path: Path, component_name: str, expected_elements: List[str]):
    """Check if component contains expected React elements"""
    if not component_path.exists():
        return
    
    try:
        content = component_path.read_text(encoding='utf-8')
        
        # Check for React component definition
        if 'export' not in content and 'function' not in content:
            print(f"{Colors.WARNING}  ⚠ {component_name}: No export found{Colors.ENDC}")
            results["warnings"] += 1
            results["issues"].append(f"{component_name}: No export found")
        
        # Check for expected elements
        missing_elements = []
        for element in expected_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"{Colors.WARNING}  ⚠ {component_name}: Missing elements: {', '.join(missing_elements)}{Colors.ENDC}")
            results["warnings"] += 1
        else:
            print(f"  {Colors.OKGREEN}✓ {component_name} structure validated{Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}  ✗ Error reading {component_name}: {str(e)}{Colors.ENDC}")
        results["failed"] += 1

def verify_page_components(frontend_dir: Path):
    """Verify all page components"""
    print_header("PAGE COMPONENTS VERIFICATION")
    
    pages_dir = frontend_dir / "src" / "pages"
    
    pages = [
        ("index.tsx", ["Home", "Link"]),
        ("dashboard.tsx", ["Dashboard", "useState"]),
        ("login.tsx", ["Login", "useState", "form"]),
        ("upload.tsx", ["Upload", "useState"]),
        ("validation.tsx", ["Validation", "useState"]),
        ("schema-validation.tsx", ["Schema", "useState"]),
        ("schema-drift.tsx", ["Drift", "useState"]),
        ("metrics.tsx", ["Metrics", "useState"]),
        ("metrics-dashboard.tsx", ["Dashboard", "useState"]),
        ("profiling-dashboard.tsx", ["Profiling", "useState"]),
        ("freshness-monitoring.tsx", ["Freshness", "useState"]),
        ("pipeline-executions.tsx", ["Pipeline", "useState"]),
        ("pipelines.tsx", ["Pipeline", "useState"]),
        ("logs.tsx", ["Logs", "useState"]),
        ("audit-history.tsx", ["Audit", "useState"]),
        ("health.tsx", ["Health", "useState"]),
        ("cache-monitoring.tsx", ["Cache", "useState"]),
        ("warehouse-status.tsx", ["Warehouse", "useState"]),
        ("warehouse-load-monitoring.tsx", ["Load", "useState"]),
        ("data-sources.tsx", ["DataSource", "useState"]),
        ("alerts.tsx", ["Alert", "useState"]),
        ("validation-retry.tsx", ["Retry", "useState"]),
        ("async-task-monitoring.tsx", ["Task", "useState"]),
        ("rules-management.tsx", ["Rules", "useState"]),
    ]
    
    for page_file, expected in pages:
        page_path = pages_dir / page_file
        check_component_exists(page_path, f"Page: {page_file}")
        if page_path.exists():
            check_component_structure(page_path, page_file, expected)

def verify_ui_components(frontend_dir: Path):
    """Verify all UI components"""
    print_header("UI COMPONENTS VERIFICATION")
    
    components_dir = frontend_dir / "src" / "components"
    
    components = {
        "Alert.tsx": ["Alert", "message"],
        "AuditHistoryTable.tsx": ["Table", "audit"],
        "CacheMetricsCard.tsx": ["Card", "cache"],
        "CacheStatusIndicator.tsx": ["Indicator", "status"],
        "CloudExecutionStatus.tsx": ["Cloud", "status"],
        "CloudObservabilitySection.tsx": ["Section", "observability"],
        "CloudWatchStatusCard.tsx": ["Card", "CloudWatch"],
        "ColumnDistributionChart.tsx": ["Chart", "distribution"],
        "ConnectionStatusIndicator.tsx": ["Indicator", "connection"],
        "DAGExecutionTable.tsx": ["Table", "execution"],
        "DAGExecutionTimeline.tsx": ["Timeline", "execution"],
        "DatasetStatisticsCard.tsx": ["Card", "statistics"],
        "DriftAlertIndicator.tsx": ["Alert", "drift"],
        "ErrorBoundary.tsx": ["ErrorBoundary", "componentDidCatch"],
        "ExecutionEnvironmentStatus.tsx": ["Environment", "status"],
        "ExportCSVButton.tsx": ["Button", "export"],
        "FailedLoadSection.tsx": ["Section", "failed"],
        "FailedPipelineSection.tsx": ["Section", "pipeline"],
        "FailureInsightsPanel.tsx": ["Panel", "insights"],
        "FallbackUI.tsx": ["Fallback", "error"],
        "FreshnessMetricsChart.tsx": ["Chart", "freshness"],
        "GlueJobStatusCard.tsx": ["Card", "Glue"],
        "HealthScoreWidget.tsx": ["Widget", "health"],
        "HealthTrendChart.tsx": ["Chart", "trend"],
        "IntegrityViolationsTable.tsx": ["Table", "violations"],
        "LatencyChart.tsx": ["Chart", "latency"],
        "LoadHistoryTable.tsx": ["Table", "history"],
        "LoadingSpinner.tsx": ["Loading", "spinner"],
        "LoadStatusIndicator.tsx": ["Indicator", "load"],
        "LogsTable.tsx": ["Table", "logs"],
        "MetricCard.tsx": ["Card", "metric"],
        "MetricsProviderStatus.tsx": ["Status", "provider"],
        "PipelinePerformanceSection.tsx": ["Section", "performance"],
        "PipelineScoreCard.tsx": ["Card", "score"],
        "PipelineSummaryCards.tsx": ["Card", "summary"],
        "ProfilingSummaryCards.tsx": ["Card", "profiling"],
        "ProtectedRoute.tsx": ["Route", "auth"],
        "QueueMetricsSection.tsx": ["Section", "queue"],
        "RetryHistoryTable.tsx": ["Table", "retry"],
        "RuleActivationToggle.tsx": ["Toggle", "rule"],
        "RulePreview.tsx": ["Preview", "rule"],
        "RulesEditor.tsx": ["Editor", "rules"],
        "SchedulerStatusIndicator.tsx": ["Indicator", "scheduler"],
        "SchemaComparisonTable.tsx": ["Table", "comparison"],
        "SchemaDriftDashboard.tsx": ["Dashboard", "drift"],
        "SchemaTimelineView.tsx": ["Timeline", "schema"],
        "SLAIndicatorCard.tsx": ["Card", "SLA"],
        "StorageProviderStatus.tsx": ["Status", "storage"],
        "Table.tsx": ["Table", "thead"],
        "TaskStatusTable.tsx": ["Table", "task"],
        "ThresholdStatusBadge.tsx": ["Badge", "threshold"],
        "ToastNotification.tsx": ["Toast", "notification"],
        "TopNavigation.tsx": ["Navigation", "nav"],
        "UploadButton.tsx": ["Button", "upload"],
        "UploadProgress.tsx": ["Progress", "upload"],
        "ValidationFilters.tsx": ["Filter", "validation"],
        "ValidationMetricsWidget.tsx": ["Widget", "metrics"],
        "ValidationResultsTable.tsx": ["Table", "results"],
        "ValidationStatusBadge.tsx": ["Badge", "status"],
        "ValidationSummaryCards.tsx": ["Card", "summary"],
        "WarehouseLoadExecutionTable.tsx": ["Table", "warehouse"],
        "WarehouseStatusWidget.tsx": ["Widget", "warehouse"],
        "WorkerStatusCard.tsx": ["Card", "worker"],
        "AirflowHealthWidget.tsx": ["Widget", "Airflow"],
    }
    
    for component_file, expected in components.items():
        component_path = components_dir / component_file
        check_component_exists(component_path, component_file)
        if component_path.exists():
            check_component_structure(component_path, component_file, expected)

def verify_api_services(frontend_dir: Path):
    """Verify API service files"""
    print_header("API SERVICES VERIFICATION")
    
    services_dir = frontend_dir / "src" / "services"
    
    if not services_dir.exists():
        print(f"{Colors.FAIL}✗ Services directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for API service files
    service_files = list(services_dir.glob("*.ts")) + list(services_dir.glob("*.tsx"))
    
    if len(service_files) == 0:
        print(f"{Colors.WARNING}⚠ No service files found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(service_files)} service files{Colors.ENDC}")
        for service_file in service_files:
            print(f"  - {service_file.name}")
            results["passed"] += 1

def verify_hooks(frontend_dir: Path):
    """Verify React hooks"""
    print_header("REACT HOOKS VERIFICATION")
    
    hooks_dir = frontend_dir / "src" / "hooks"
    
    if not hooks_dir.exists():
        print(f"{Colors.WARNING}⚠ Hooks directory not found{Colors.ENDC}")
        results["warnings"] += 1
        return
    
    # Check for custom hooks
    hook_files = list(hooks_dir.glob("*.ts")) + list(hooks_dir.glob("*.tsx"))
    
    if len(hook_files) == 0:
        print(f"{Colors.WARNING}⚠ No custom hooks found{Colors.ENDC}")
        results["warnings"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(hook_files)} custom hooks{Colors.ENDC}")
        for hook_file in hook_files:
            print(f"  - {hook_file.name}")
            results["passed"] += 1

def verify_test_files(frontend_dir: Path):
    """Verify test files exist for components"""
    print_header("TEST FILES VERIFICATION")
    
    tests_dir = frontend_dir / "__tests__"
    
    if not tests_dir.exists():
        print(f"{Colors.FAIL}✗ Tests directory not found{Colors.ENDC}")
        results["failed"] += 1
        return
    
    # Check for test files
    test_files = list(tests_dir.rglob("*.test.tsx")) + list(tests_dir.rglob("*.test.ts"))
    
    if len(test_files) == 0:
        print(f"{Colors.FAIL}✗ No test files found{Colors.ENDC}")
        results["failed"] += 1
    else:
        print(f"{Colors.OKGREEN}✓ Found {len(test_files)} test files{Colors.ENDC}")
        for test_file in test_files:
            print(f"  - {test_file.relative_to(tests_dir)}")
            results["passed"] += 1

def verify_config_files(frontend_dir: Path):
    """Verify configuration files"""
    print_header("CONFIGURATION FILES VERIFICATION")
    
    config_files = [
        ("package.json", ["dependencies", "scripts"]),
        ("tsconfig.json", ["compilerOptions"]),
        ("next.config.js", ["nextConfig"]),
        ("tailwind.config.js", ["content", "theme"]),
        ("jest.config.js", ["testEnvironment"]),
    ]
    
    for config_file, expected in config_files:
        config_path = frontend_dir / config_file
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

def verify_routing(frontend_dir: Path):
    """Verify routing configuration"""
    print_header("ROUTING VERIFICATION")
    
    # Check if pages exist for routing
    pages_dir = frontend_dir / "src" / "pages"
    
    if pages_dir.exists():
        page_files = list(pages_dir.glob("*.tsx"))
        api_routes = list((pages_dir / "api").glob("*.ts")) if (pages_dir / "api").exists() else []
        
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} Found {len(page_files)} pages")
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} Found {len(api_routes)} API routes")
        results["passed"] += 2
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC} Pages directory not found")
        results["failed"] += 1

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
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL COMPONENTS VERIFIED SUCCESSFULLY!{Colors.ENDC}")
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
    print("UI COMPONENTS COMPREHENSIVE VERIFICATION".center(80))
    print("="*80)
    print(f"{Colors.ENDC}\n")
    
    # Get project directory
    project_dir = Path(__file__).parent
    frontend_dir = project_dir / "frontend"
    
    if not frontend_dir.exists():
        print(f"{Colors.FAIL}ERROR: Frontend directory not found!{Colors.ENDC}")
        print(f"Expected path: {frontend_dir}")
        return 1
    
    print(f"Frontend directory: {frontend_dir}")
    
    # Run verification suites
    verify_config_files(frontend_dir)
    verify_page_components(frontend_dir)
    verify_ui_components(frontend_dir)
    verify_api_services(frontend_dir)
    verify_hooks(frontend_dir)
    verify_test_files(frontend_dir)
    verify_routing(frontend_dir)
    
    # Print summary
    return print_summary()

if __name__ == "__main__":
    import sys
    sys.exit(main())
