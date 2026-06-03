"""Sample Audit Data Generator

Generates synthetic audit records for testing and development purposes.
Populates the PostgreSQL database with realistic audit history.
"""
import random
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.audit_service import AuditService


# Sample data configurations
DATASETS = [
    "customer_data",
    "orders",
    "products",
    "inventory",
    "transactions",
    "user_profiles",
    "sales_records",
    "financial_reports",
]

VALIDATION_TYPES = [
    "schema",
    "null",
    "datatype",
    "checksum",
    "integrity",
    "aggregated",
    "referential_integrity",
    "completeness",
]

STATUSES = ["passed", "failed", "warning", "error"]
STATUS_WEIGHTS = [0.6, 0.2, 0.15, 0.05]  # 60% passed, 20% failed, 15% warning, 5% error

VALIDATORS = [
    "SchemaValidator",
    "NullValidator",
    "DataTypeValidator",
    "ChecksumValidator",
    "ReferentialIntegrityValidator",
    "CompletenessValidator",
    "AggregationValidator",
]

TRIGGERED_BY = ["system", "scheduler", "manual", "api", "user_admin"]
ENVIRONMENTS = ["dev", "staging", "production"]


def generate_random_audit_record() -> dict:
    """Generate a single random audit record"""
    
    dataset_name = random.choice(DATASETS)
    validation_type = random.choice(VALIDATION_TYPES)
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    
    # Generate realistic metrics based on status
    total_records = random.randint(100, 100000)
    if status == "passed":
        failed_records = random.randint(0, int(total_records * 0.01))
    elif status == "failed":
        failed_records = random.randint(int(total_records * 0.1), int(total_records * 0.5))
    elif status == "warning":
        failed_records = random.randint(int(total_records * 0.02), int(total_records * 0.1))
    else:  # error
        failed_records = total_records
    
    pass_rate = ((total_records - failed_records) / total_records) * 100 if total_records > 0 else 0.0
    
    # Execution time based on dataset size
    execution_time_ms = random.uniform(100, 5000) + (total_records / 1000)
    
    # Error summary for non-passed statuses
    error_summary = None
    if status != "passed":
        error_summaries = [
            "Data type mismatch detected in multiple columns",
            "Schema validation failed: missing required columns",
            "Null values found in non-nullable columns",
            "Checksum validation failed: data integrity compromised",
            "Referential integrity constraint violated",
            "Duplicate primary keys detected",
            "Foreign key constraint violation",
            "Data completeness check failed",
        ]
        error_summary = random.choice(error_summaries)
    
    # Metadata
    metadata = {
        "version": f"v{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 50)}",
        "data_source": random.choice(["s3", "database", "api", "file_upload"]),
        "tags": random.sample(["production", "critical", "scheduled", "adhoc", "monitoring"], k=random.randint(1, 3)),
    }
    
    # Details
    details = {
        "validation_rules": random.randint(5, 20),
        "columns_validated": random.randint(10, 50),
        "rows_scanned": total_records,
    }
    
    if status in ["failed", "error"]:
        details["error_count"] = random.randint(1, 50)
        details["error_types"] = random.sample(
            ["type_mismatch", "null_violation", "constraint_violation", "format_error"],
            k=random.randint(1, 3)
        )
    
    return {
        "dataset_name": dataset_name,
        "validation_type": validation_type,
        "status": status,
        "execution_time_ms": round(execution_time_ms, 2),
        "total_records": total_records,
        "failed_records": failed_records,
        "pass_rate": round(pass_rate, 2),
        "validator_name": random.choice(VALIDATORS),
        "triggered_by": random.choice(TRIGGERED_BY),
        "environment": random.choice(ENVIRONMENTS),
        "metadata": metadata,
        "error_summary": error_summary,
        "details": details,
    }


def generate_audit_history(
    db: Session,
    num_records: int = 100,
    days_back: int = 30
) -> List[dict]:
    """
    Generate and insert synthetic audit history records.
    
    Args:
        db: Database session
        num_records: Number of audit records to generate
        days_back: Generate records spanning this many days in the past
        
    Returns:
        List of generated audit record dictionaries
    """
    service = AuditService(db)
    generated_records = []
    
    print(f"Generating {num_records} audit records spanning {days_back} days...")
    
    for i in range(num_records):
        # Generate random record
        record_data = generate_random_audit_record()
        
        # Create the audit record
        audit_log = service.create_audit_record(**record_data)
        
        # Backdate the created_at timestamp to simulate historical data
        random_days_ago = random.uniform(0, days_back)
        backdated_timestamp = datetime.utcnow() - timedelta(days=random_days_ago)
        
        # Update the timestamp directly
        audit_log.created_at = backdated_timestamp
        audit_log.updated_at = backdated_timestamp
        db.commit()
        
        generated_records.append({
            "id": audit_log.id,
            "dataset_name": audit_log.dataset_name,
            "validation_type": audit_log.validation_type,
            "status": audit_log.status,
            "created_at": audit_log.created_at.isoformat(),
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_records} records...")
    
    print(f"✓ Successfully generated {num_records} audit records!")
    return generated_records


def seed_audit_data(num_records: int = 100, days_back: int = 30):
    """
    Main function to seed the database with sample audit data.
    
    Args:
        num_records: Number of audit records to generate
        days_back: Generate records spanning this many days in the past
    """
    print("\n" + "=" * 60)
    print("AUDIT DATA SEED GENERATOR")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        records = generate_audit_history(db, num_records, days_back)
        
        print("\n" + "=" * 60)
        print("SEED SUMMARY")
        print("=" * 60)
        print(f"Total records generated: {len(records)}")
        
        # Get statistics
        service = AuditService(db)
        stats = service.get_audit_statistics()
        
        print(f"\nStatus distribution:")
        for status, count in stats["status_distribution"].items():
            print(f"  {status}: {count}")
        
        print(f"\nValidation type distribution:")
        for vtype, count in stats["validation_type_distribution"].items():
            print(f"  {vtype}: {count}")
        
        print(f"\nAverage execution time: {stats['average_execution_time_ms']:.2f}ms")
        
        print("\n" + "=" * 60)
        print("✓ Seed data generation completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error generating seed data: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Generate 100 audit records spanning the last 30 days
    seed_audit_data(num_records=100, days_back=30)
