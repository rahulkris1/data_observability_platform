"""
Data Quality Pipeline DAG
Orchestrates data ingestion, validation, and audit logging
"""
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

import psycopg2
from pyspark.sql import SparkSession

# Add backend to Python path
ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(ROOT))

from app.services.ingestion_service import IngestionService
from app.services.validation_aggregator import ValidationAggregator
from app.services.audit_service import AuditService
from app.services.dag_execution_service import DAGExecutionService
from app.services.glue_service import get_glue_service
from app.validators import SchemaValidator, NullValidator, DatatypeValidator, ChecksumValidator, ColumnExistenceValidator
from app.core.database import get_db
from app.core.config import settings
from app.utils.spark_utils import get_spark_session


# DAG default arguments
default_args = {
    'owner': 'data-observability',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}


def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host='postgres',
        port=5432,
        user='dop_user',
        password='dop_password',
        database='data_observability'
    )


def log_dag_execution(dag_run_id: str, state: str, **context):
    """
    Log DAG execution to PostgreSQL.
    
    Args:
        dag_run_id: Unique DAG run identifier
        state: Execution state
        **context: Airflow context
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine('postgresql://dop_user:dop_password@postgres:5432/data_observability')
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        service = DAGExecutionService(db)
        execution_date = context['execution_date']
        
        # Check if record exists
        existing = service.get_execution_by_run_id(dag_run_id)
        
        if not existing:
            # Create new record
            service.create_execution_record(
                dag_id=context['dag'].dag_id,
                dag_run_id=dag_run_id,
                execution_date=execution_date,
                state=state,
                run_type=context['dag_run'].run_type,
                conf=context['dag_run'].conf if hasattr(context['dag_run'], 'conf') else {},
                start_date=datetime.utcnow()
            )
            print(f"✓ Created DAG execution record: {dag_run_id}")
        else:
            # Update existing record
            end_date = datetime.utcnow() if state in ['success', 'failed'] else None
            service.update_execution_record(
                dag_run_id=dag_run_id,
                state=state,
                end_date=end_date
            )
            print(f"✓ Updated DAG execution record: {dag_run_id} -> {state}")
    
    finally:
        db.close()


def ingest_dataset(**context):
    """
    Task: Ingest dataset into MinIO.
    Uses a sample test dataset for demonstration.
    """
    dag_run_id = context['dag_run'].run_id
    task_start = datetime.utcnow()
    
    print(f"Starting ingestion task for DAG run: {dag_run_id}")
    
    try:
        # Log task start
        log_dag_execution(dag_run_id, 'running', **context)
        
        # Get dataset path from DAG run config or use default
        conf = context['dag_run'].conf or {}
        dataset_path = conf.get('dataset_path', '/opt/airflow/tests/fixtures/sample_customers.csv')
        
        print(f"Ingesting dataset: {dataset_path}")
        
        # Read dataset file
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        file_bytes = dataset_file.read_bytes()
        
        # Ingest using service
        service = IngestionService()
        result = service.ingest_dataset(dataset_file.name, file_bytes)
        
        print(f"✓ Ingestion completed: {result['record_count']} records")
        print(f"  Raw object: {result['raw_object_name']}")
        print(f"  Processed object: {result['processed_object_name']}")
        
        # Store result in XCom for next tasks
        context['task_instance'].xcom_push(key='ingestion_result', value=result)
        
        task_end = datetime.utcnow()
        duration = (task_end - task_start).total_seconds()
        print(f"✓ Ingestion task completed in {duration:.2f}s")
        
        return result
    
    except Exception as e:
        print(f"✗ Ingestion task failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise


def validate_dataset(**context):
    """
    Task: Validate ingested dataset using validation services.
    """
    dag_run_id = context['dag_run'].run_id
    task_start = datetime.utcnow()
    
    print(f"Starting validation task for DAG run: {dag_run_id}")
    
    try:
        # Get ingestion result from previous task
        ingestion_result = context['task_instance'].xcom_pull(
            task_ids='ingest_dataset',
            key='ingestion_result'
        )
        
        if not ingestion_result:
            raise ValueError("No ingestion result found from previous task")
        
        processed_object = ingestion_result['processed_object_name']
        print(f"Validating processed object: {processed_object}")
        
        # Load processed dataset
        service = IngestionService()
        dataset = service.load_processed_dataset(processed_object)
        
        # Create Spark DataFrame
        spark = get_spark_session()
        df = spark.createDataFrame(dataset)
        
        print(f"Created DataFrame with {df.count()} rows and {len(df.columns)} columns")
        
        # Create validation aggregator and add validators
        aggregator = ValidationAggregator()
        
        # Get schema contract from DAG run config if provided
        conf = context['dag_run'].conf or {}
        schema_contract = conf.get('schema_contract')
        
        if schema_contract:
            print(f"Using provided schema contract")
            validation_summary = aggregator.validate_with_defaults(
                df=df,
                dataset_name=ingestion_result['filename'],
                schema_contract=schema_contract
            )
        else:
            print("Running basic validation without schema contract")
            # Add basic validators
            aggregator.add_validator(NullValidator(max_null_percentage=5.0))
            aggregator.add_validator(ChecksumValidator())
            
            validation_summary = aggregator.validate(
                df=df,
                dataset_name=ingestion_result['filename']
            )
        
        # Convert validation summary to dict
        validation_result = {
            'dataset_name': validation_summary.dataset_name,
            'total_validations': validation_summary.total_validations,
            'passed_validations': validation_summary.passed_validations,
            'failed_validations': validation_summary.failed_validations,
            'overall_status': validation_summary.overall_status,
            'validation_timestamp': validation_summary.validation_timestamp.isoformat(),
            'validators': [
                {
                    'name': v.validator_name,
                    'status': v.status,
                    'pass_rate': v.pass_rate
                }
                for v in validation_summary.validators
            ]
        }
        
        print(f"✓ Validation completed: {validation_summary.overall_status}")
        print(f"  Passed: {validation_summary.passed_validations}/{validation_summary.total_validations}")
        
        # Store result in XCom
        context['task_instance'].xcom_push(key='validation_result', value=validation_result)
        
        task_end = datetime.utcnow()
        duration = (task_end - task_start).total_seconds()
        print(f"✓ Validation task completed in {duration:.2f}s")
        
        return validation_result
    
    except Exception as e:
        print(f"✗ Validation task failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise


def audit_logging(**context):
    """
    Task: Log validation results to audit table.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    dag_run_id = context['dag_run'].run_id
    task_start = datetime.utcnow()
    
    print(f"Starting audit logging task for DAG run: {dag_run_id}")
    
    try:
        # Get validation result from previous task
        validation_result = context['task_instance'].xcom_pull(
            task_ids='validate_dataset',
            key='validation_result'
        )
        
        if not validation_result:
            raise ValueError("No validation result found from previous task")
        
        # Get ingestion result
        ingestion_result = context['task_instance'].xcom_pull(
            task_ids='ingest_dataset',
            key='ingestion_result'
        )
        
        # Create database session
        engine = create_engine('postgresql://dop_user:dop_password@postgres:5432/data_observability')
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            audit_service = AuditService(db)
            
            # Create audit record for each validator
            for validator_info in validation_result['validators']:
                audit_record = audit_service.create_audit_record(
                    dataset_name=validation_result['dataset_name'],
                    validation_type=validator_info['name'],
                    status=validator_info['status'],
                    total_records=ingestion_result.get('record_count', 0),
                    pass_rate=validator_info['pass_rate'],
                    validator_name=validator_info['name'],
                    triggered_by='airflow',
                    environment='local',
                    metadata={
                        'dag_run_id': dag_run_id,
                        'dag_id': context['dag'].dag_id,
                        'execution_date': context['execution_date'].isoformat()
                    }
                )
                print(f"✓ Created audit record for {validator_info['name']}: {audit_record.id}")
            
            print(f"✓ Audit logging completed: {len(validation_result['validators'])} records")
        
        finally:
            db.close()
        
        task_end = datetime.utcnow()
        duration = (task_end - task_start).total_seconds()
        print(f"✓ Audit logging task completed in {duration:.2f}s")
        
        return {"audit_records": len(validation_result['validators'])}
    
    except Exception as e:
        print(f"✗ Audit logging task failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise


def pipeline_completion(**context):
    """
    Task: Mark pipeline as complete and update DAG execution metadata.
    """
    dag_run_id = context['dag_run'].run_id
    
    print(f"Pipeline completion for DAG run: {dag_run_id}")
    
    try:
        # Gather all task results
        ingestion_result = context['task_instance'].xcom_pull(
            task_ids='ingest_dataset',
            key='ingestion_result'
        )
        validation_result = context['task_instance'].xcom_pull(
            task_ids='validate_dataset',
            key='validation_result'
        )
        
        # Update DAG execution with task details
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine('postgresql://dop_user:dop_password@postgres:5432/data_observability')
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            service = DAGExecutionService(db)
            service.update_execution_record(
                dag_run_id=dag_run_id,
                state='success',
                end_date=datetime.utcnow(),
                total_tasks=4,
                completed_tasks=4,
                failed_tasks=0,
                task_details={
                    'ingestion': {
                        'status': 'success',
                        'records': ingestion_result.get('record_count', 0) if ingestion_result else 0
                    },
                    'validation': {
                        'status': 'success',
                        'overall_status': validation_result.get('overall_status') if validation_result else 'unknown',
                        'passed': validation_result.get('passed_validations', 0) if validation_result else 0,
                        'failed': validation_result.get('failed_validations', 0) if validation_result else 0
                    },
                    'audit': {
                        'status': 'success'
                    }
                }
            )
            
            print(f"✓ Pipeline completed successfully")
            print(f"  DAG run: {dag_run_id}")
            print(f"  Records ingested: {ingestion_result.get('record_count', 0) if ingestion_result else 0}")
            print(f"  Validation status: {validation_result.get('overall_status') if validation_result else 'unknown'}")
        
        finally:
            db.close()
        
        return {"status": "completed"}
    
    except Exception as e:
        print(f"✗ Pipeline completion failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise


def trigger_glue_job(**context):
    """
    Task: Trigger AWS Glue job for cloud-based data processing.
    
    This task runs only when EXECUTION_MODE is set to 'glue'.
    """
    dag_run_id = context['dag_run'].run_id
    task_start = datetime.utcnow()
    
    print(f"Triggering Glue job for DAG run: {dag_run_id}")
    
    try:
        # Check execution mode
        if settings.EXECUTION_MODE.lower() != 'glue':
            print(f"⚠ Execution mode is '{settings.EXECUTION_MODE}', skipping Glue job trigger")
            return {"status": "skipped", "reason": "execution_mode_not_glue"}
        
        # Get Glue service
        glue_service = get_glue_service()
        
        if not glue_service.is_available():
            raise RuntimeError("Glue service is not available. Check AWS credentials and configuration.")
        
        # Get DAG run configuration
        conf = context['dag_run'].conf or {}
        source_path = conf.get('source_path', f"s3://{settings.S3_BUCKET_RAW}/")
        file_format = conf.get('file_format', 'json')
        
        # Prepare Glue job arguments
        job_arguments = {
            '--SOURCE_PATH': source_path,
            '--FILE_FORMAT': file_format,
            '--OUTPUT_FORMAT': 'parquet',
            '--DAG_RUN_ID': dag_run_id
        }
        
        print(f"Starting Glue job: {settings.GLUE_JOB_NAME}")
        print(f"  Source: {source_path}")
        print(f"  Format: {file_format}")
        
        # Start Glue job run
        job_run_id = glue_service.start_job_run(job_arguments=job_arguments)
        
        if not job_run_id:
            raise RuntimeError("Failed to start Glue job run")
        
        print(f"✓ Glue job started successfully")
        print(f"  Job Run ID: {job_run_id}")
        
        # Store job run ID for monitoring
        context['task_instance'].xcom_push(key='glue_job_run_id', value=job_run_id)
        
        # Monitor job status (optional - can be done in separate task)
        import time
        max_wait_time = 300  # 5 minutes
        check_interval = 30  # 30 seconds
        elapsed = 0
        
        while elapsed < max_wait_time:
            status = glue_service.get_job_run_status(job_run_id=job_run_id)
            
            if status:
                state = status.get('state')
                print(f"  Glue job state: {state}")
                
                if state in ['SUCCEEDED', 'FAILED', 'STOPPED', 'TIMEOUT']:
                    break
            
            time.sleep(check_interval)
            elapsed += check_interval
        
        # Get final status
        final_status = glue_service.get_job_run_status(job_run_id=job_run_id)
        
        if final_status:
            final_state = final_status.get('state')
            execution_time = final_status.get('execution_time', 0)
            
            print(f"✓ Glue job final state: {final_state}")
            print(f"  Execution time: {execution_time}s")
            
            if final_state == 'FAILED':
                error_msg = final_status.get('error_message', 'Unknown error')
                raise RuntimeError(f"Glue job failed: {error_msg}")
        
        task_end = datetime.utcnow()
        duration = (task_end - task_start).total_seconds()
        print(f"✓ Glue job task completed in {duration:.2f}s")
        
        return {
            "status": "success",
            "job_run_id": job_run_id,
            "execution_time": execution_time,
            "glue_state": final_state
        }
    
    except Exception as e:
        print(f"✗ Glue job trigger failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise
        
        engine = create_engine('postgresql://dop_user:dop_password@postgres:5432/data_observability')
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            service = DAGExecutionService(db)
            service.update_execution_record(
                dag_run_id=dag_run_id,
                state='success',
                end_date=datetime.utcnow(),
                total_tasks=4,
                completed_tasks=4,
                failed_tasks=0,
                task_details={
                    'ingestion': {
                        'status': 'success',
                        'records': ingestion_result.get('record_count', 0) if ingestion_result else 0
                    },
                    'validation': {
                        'status': 'success',
                        'overall_status': validation_result.get('overall_status') if validation_result else 'unknown',
                        'passed': validation_result.get('passed_validations', 0) if validation_result else 0,
                        'failed': validation_result.get('failed_validations', 0) if validation_result else 0
                    },
                    'audit': {
                        'status': 'success'
                    }
                }
            )
            
            print(f"✓ Pipeline completed successfully")
            print(f"  DAG run: {dag_run_id}")
            print(f"  Records ingested: {ingestion_result.get('record_count', 0) if ingestion_result else 0}")
            print(f"  Validation status: {validation_result.get('overall_status') if validation_result else 'unknown'}")
        
        finally:
            db.close()
        
        return {"status": "completed"}
    
    except Exception as e:
        print(f"✗ Pipeline completion failed: {e}")
        log_dag_execution(dag_run_id, 'failed', **context)
        raise


# Create DAG
with DAG(
    dag_id='data_quality_pipeline',
    default_args=default_args,
    description='Data quality pipeline: ingestion → validation → audit',
    schedule_interval='@daily',  # Run daily
    start_date=days_ago(1),
    catchup=False,
    tags=['data-quality', 'validation', 'observability'],
    max_active_runs=3,
) as dag:
    
    # Task 1: Ingest dataset
    ingest_task = PythonOperator(
        task_id='ingest_dataset',
        python_callable=ingest_dataset,
        provide_context=True,
        doc_md="""
        ## Ingest Dataset
        
        Ingests a dataset file into MinIO storage.
        
        - Reads local file or uses configured path
        - Uploads raw data to MinIO
        - Parses and uploads processed data
        - Returns ingestion metadata
        """,
    )
    
    # Task 2: Validate dataset
    validate_task = PythonOperator(
        task_id='validate_dataset',
        python_callable=validate_dataset,
        provide_context=True,
        doc_md="""
        ## Validate Dataset
        
        Runs validation checks on ingested dataset.
        
        - Loads processed dataset from MinIO
        - Creates Spark DataFrame
        - Runs multiple validators
        - Returns validation summary
        """,
    )
    
    # Task 3: Audit logging
    audit_task = PythonOperator(
        task_id='audit_logging',
        python_callable=audit_logging,
        provide_context=True,
        doc_md="""
        ## Audit Logging
        
        Logs validation results to audit table.
        
        - Creates audit records for each validator
        - Stores execution metadata
        - Links to DAG run information
        """,
    )
    
    # Task 4: Trigger Glue Job (optional, runs in cloud mode)
    glue_job_task = PythonOperator(
        task_id='trigger_glue_job',
        python_callable=trigger_glue_job,
        provide_context=True,
        doc_md="""
        ## Trigger AWS Glue Job
        
        Triggers AWS Glue job for cloud-based processing.
        
        - Runs only when EXECUTION_MODE='glue'
        - Starts Glue job with configured parameters
        - Monitors job execution status
        - Skipped in local mode
        """,
    )
    
    # Task 5: Pipeline completion
    completion_task = PythonOperator(
        task_id='pipeline_completion',
        python_callable=pipeline_completion,
        provide_context=True,
        doc_md="""
        ## Pipeline Completion
        
        Finalizes pipeline execution.
        
        - Updates DAG execution metadata
        - Stores task-level details
        - Marks pipeline as complete
        """,
    )
    
    # Define task dependencies
    # Local mode: ingestion → validation → audit → completion
    # Glue mode: ingestion → glue_job → validation → audit → completion
    ingest_task >> validate_task >> audit_task >> completion_task
    
    # Add Glue job trigger as parallel task after ingestion
    # It can run alongside local validation for flexibility
    ingest_task >> glue_job_task >> completion_task
