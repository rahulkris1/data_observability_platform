"""
Data Observability Platform - Health Check DAG
Simple DAG to verify Airflow is working correctly
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


default_args = {
    'owner': 'data-observability',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def check_platform_health():
    """Check basic platform connectivity"""
    import psycopg2
    from minio import Minio
    import redis
    
    checks = {
        'postgres': False,
        'minio': False,
        'redis': False,
    }
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(
            host='postgres',
            port=5432,
            user='dop_user',
            password='dop_password',
            database='data_observability'
        )
        conn.close()
        checks['postgres'] = True
        print("✓ PostgreSQL connection successful")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
    
    # Check MinIO
    try:
        minio_client = Minio(
            'minio:9000',
            access_key='minioadmin',
            secret_key='minioadmin123',
            secure=False
        )
        buckets = minio_client.list_buckets()
        checks['minio'] = True
        print(f"✓ MinIO connection successful ({len(buckets)} buckets found)")
    except Exception as e:
        print(f"✗ MinIO connection failed: {e}")
    
    # Check Redis
    try:
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        checks['redis'] = True
        print("✓ Redis connection successful")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
    
    # Summary
    all_healthy = all(checks.values())
    status = "✓ All services healthy" if all_healthy else "✗ Some services unhealthy"
    print(f"\n{status}")
    print(f"Results: {checks}")
    
    return checks


def log_execution_info(**context):
    """Log DAG execution information"""
    execution_date = context['execution_date']
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    
    print(f"DAG ID: {dag_id}")
    print(f"Task ID: {task_id}")
    print(f"Execution Date: {execution_date}")
    print(f"Current Time: {datetime.now()}")
    

with DAG(
    'dop_health_check',
    default_args=default_args,
    description='Data Observability Platform health check',
    schedule=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['health', 'monitoring'],
) as dag:
    
    # Task 1: Log execution info
    log_task = PythonOperator(
        task_id='log_execution_info',
        python_callable=log_execution_info,
        provide_context=True,
    )
    
    # Task 2: Check platform health
    health_check_task = PythonOperator(
        task_id='check_platform_health',
        python_callable=check_platform_health,
    )
    
    # Task 3: Echo completion
    completion_task = BashOperator(
        task_id='completion_message',
        bash_command='echo "Health check completed successfully at $(date)"',
    )
    
    # Define task dependencies
    log_task >> health_check_task >> completion_task
