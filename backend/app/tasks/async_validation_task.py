"""
Async Celery tasks for data validation.
"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.celery_app import celery_app
from app.services.schema_contract_service import get_schema_contract_service
from app.validators.validation_rules_engine import ValidationRulesEngine


@celery_app.task(bind=True, name="validate_dataset_async")
def validate_dataset_async(
    self,
    contract_name: str,
    dataset_columns: List[Dict[str, Any]],
    dataset_name: str,
) -> Dict[str, Any]:
    """
    Asynchronously validate a dataset against a schema contract.
    
    Args:
        self: Task instance (injected by Celery)
        contract_name: Name of the schema contract to validate against
        dataset_columns: List of dataset column definitions
        dataset_name: Name of the dataset being validated
        
    Returns:
        Dictionary containing validation results
    """
    start_time = time.time()
    
    # Update task state to running
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "dataset": dataset_name,
            "contract": contract_name,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    try:
        # Get service and perform validation
        service = get_schema_contract_service()
        result = service.validate_dataset(
            contract_name=contract_name,
            dataset_columns=dataset_columns,
        )
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "dataset": dataset_name,
            "contract": contract_name,
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Log the error
        error_msg = f"Validation failed: {str(e)}"
        
        return {
            "status": "failed",
            "dataset": dataset_name,
            "contract": contract_name,
            "error": error_msg,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="run_validation_rules_async")
def run_validation_rules_async(
    self,
    dataset_path: str,
    rules_config_path: str,
    dataset_name: str,
) -> Dict[str, Any]:
    """
    Asynchronously run validation rules against a dataset using the rules engine.
    
    Args:
        self: Task instance (injected by Celery)
        dataset_path: Path to the dataset file
        rules_config_path: Path to the validation rules JSON configuration
        dataset_name: Name of the dataset being validated
        
    Returns:
        Dictionary containing validation results
    """
    start_time = time.time()
    
    # Update task state to running
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "dataset": dataset_name,
            "rules_config": rules_config_path,
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    try:
        # Initialize validation engine
        engine = ValidationRulesEngine(config_path=rules_config_path)
        
        # Load dataset (simplified - in production, use proper Spark session)
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.appName("ValidationTask").getOrCreate()
        df = spark.read.csv(dataset_path, header=True, inferSchema=True)
        
        # Execute validation rules
        results = engine.execute_validation(df, dataset_name=dataset_name)
        
        # Calculate summary stats
        total_rules = len(results)
        passed_rules = sum(1 for r in results if r.status == "PASSED")
        failed_rules = sum(1 for r in results if r.status == "FAILED")
        
        execution_time = time.time() - start_time
        
        return {
            "status": "completed",
            "dataset": dataset_name,
            "total_rules": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": failed_rules,
            "results": [
                {
                    "rule_name": r.rule_name,
                    "status": r.status,
                    "message": r.message,
                    "severity": getattr(r, "severity", "INFO"),
                }
                for r in results
            ],
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        error_msg = f"Validation rules execution failed: {str(e)}"
        
        return {
            "status": "failed",
            "dataset": dataset_name,
            "error": error_msg,
            "execution_time": execution_time,
            "completed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, name="batch_validate_datasets")
def batch_validate_datasets(
    self,
    validations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Asynchronously validate multiple datasets in a batch.
    
    Args:
        self: Task instance (injected by Celery)
        validations: List of validation configurations
        
    Returns:
        Dictionary containing batch validation results
    """
    start_time = time.time()
    
    self.update_state(
        state="RUNNING",
        meta={
            "status": "running",
            "total_validations": len(validations),
            "started_at": datetime.utcnow().isoformat(),
        }
    )
    
    results = []
    
    for idx, validation in enumerate(validations):
        try:
            # Update progress
            self.update_state(
                state="RUNNING",
                meta={
                    "status": "running",
                    "current": idx + 1,
                    "total": len(validations),
                }
            )
            
            # Perform validation
            service = get_schema_contract_service()
            result = service.validate_dataset(
                contract_name=validation["contract_name"],
                dataset_columns=validation["dataset_columns"],
            )
            
            results.append({
                "dataset": validation.get("dataset_name", f"dataset_{idx}"),
                "is_valid": result.is_valid,
                "errors": result.errors,
            })
            
        except Exception as e:
            results.append({
                "dataset": validation.get("dataset_name", f"dataset_{idx}"),
                "error": str(e),
            })
    
    execution_time = time.time() - start_time
    
    return {
        "status": "completed",
        "total_validations": len(validations),
        "results": results,
        "execution_time": execution_time,
        "completed_at": datetime.utcnow().isoformat(),
    }
