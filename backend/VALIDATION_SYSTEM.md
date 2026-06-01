# Validation System Implementation Guide

This document describes the newly implemented validation features for the Data Observability Platform.

## Overview

The validation system provides comprehensive data quality checks with the following capabilities:

- **Multiple Validators**: Schema, null, datatype, checksum, and column existence validation
- **Validation Aggregation**: Combine results from multiple validators
- **Persistent Logging**: Store validation results in PostgreSQL
- **Metrics & Analytics**: Track validation trends and quality scores
- **Frontend Components**: Rich UI components for displaying validation data

## Backend Components

### 1. Validators

Located in `backend/app/validators/`

#### DatatypeValidator
Validates data types and type-specific rules.

```python
from app.validators import DatatypeValidator

validator = DatatypeValidator(
    column_types={
        'id': 'integer',
        'name': 'string',
        'email': 'string',
        'age': 'integer',
        'salary': 'float',
        'is_active': 'boolean'
    },
    string_patterns={
        'email': r'^[\w\.-]+@[\w\.-]+\.\w+$'
    },
    numeric_ranges={
        'age': (0, 120),
        'salary': (0, 1000000)
    }
)

result = validator.validate(df)
```

#### NullValidator (Enhanced)
Calculates null percentage per column with configurable thresholds.

```python
from app.validators import NullValidator

validator = NullValidator(
    non_null_columns=['id', 'email'],
    max_null_percentage=5.0,
    column_thresholds={
        'age': 10.0,
        'salary': 15.0
    }
)

result = validator.validate(df)
```

#### ColumnExistenceValidator
Validates required columns against schema contracts.

```python
from app.validators import ColumnExistenceValidator

validator = ColumnExistenceValidator(
    required_columns=['id', 'name', 'email'],
    optional_columns=['phone', 'address'],
    allow_extra_columns=True,
    case_sensitive=False
)

result = validator.validate(df)
```

### 2. Validation Aggregator

Located in `backend/app/services/validation_aggregator.py`

Aggregates results from multiple validators into a unified summary.

```python
from app.services.validation_aggregator import ValidationAggregator

# Create aggregator
aggregator = ValidationAggregator()

# Add validators
aggregator.add_validator(schema_validator)
aggregator.add_validator(null_validator)
aggregator.add_validator(datatype_validator)
aggregator.add_validator(column_validator)

# Execute validation
summary = aggregator.validate(df, dataset_name="customers")

# Or use default validator set
summary = aggregator.validate_with_defaults(
    df, 
    dataset_name="customers",
    schema_contract=schema_contract,
    null_threshold=5.0
)
```

### 3. Validation Log Service

Located in `backend/app/services/validation_log_service.py`

Stores and retrieves validation results from PostgreSQL.

```python
from app.services.validation_log_service import ValidationLogService

service = ValidationLogService(db)

# Log validation summary
log_entries = service.log_validation_summary(summary)

# Get validation history with filters
history = service.get_validation_history(
    dataset_name="customers",
    validation_type="schema",
    status="failed",
    limit=100
)

# Get validation metrics
metrics = service.get_validation_metrics(
    dataset_name="customers",
    days=30
)

# Get dataset statistics
stats = service.get_dataset_statistics("customers")
```

### 4. Database Models

#### ValidationLog Model
Located in `backend/app/models/validation_log.py`

Stores validation execution results:
- `dataset_name`: Name of validated dataset
- `validation_type`: Type of validation
- `status`: Validation status (passed/failed/warning/error)
- `total_records`: Total records validated
- `failed_records`: Number of failed records
- `pass_rate`: Pass percentage (0-100)
- `execution_time_ms`: Execution time in milliseconds
- `validator_name`: Name of the validator
- `message`: Human-readable message
- `details`: JSON details
- `errors`: JSON array of errors

### 5. Response Schemas

Located in `backend/app/schemas/validation_schema.py`

- `ValidatorSummary`: Summary for a single validator execution
- `ValidationSummary`: Aggregated summary of all validations
- `ValidationHistoryItem`: Single validation history record
- `ValidationMetrics`: Validation metrics for dashboard

## Frontend Components

### 1. ValidationMetricsWidget

Located in `frontend/src/components/ValidationMetricsWidget.tsx`

Displays validation metrics with four metric cards:
- Total validations executed
- Passed validations count
- Failed validations count
- Warning validations count

```tsx
import { ValidationMetricsWidget } from '@/components';

<ValidationMetricsWidget
  metrics={metrics}
  loading={isLoading}
  emptyMessage="No validation data available"
/>
```

### 2. DatasetStatisticsCard

Located in `frontend/src/components/DatasetStatisticsCard.tsx`

Displays dataset statistics:
- Dataset name
- Row count
- Column count
- Validation score (with color-coded indicator)
- Last validated timestamp

```tsx
import { DatasetStatisticsCard } from '@/components';

<DatasetStatisticsCard
  statistics={statistics}
  loading={isLoading}
  emptyMessage="No dataset statistics available"
/>
```

### 3. ValidationFilters

Located in `frontend/src/components/ValidationFilters.tsx`

Provides filtering capabilities:
- Filter by dataset name
- Filter by validation type
- Filter by validation status

```tsx
import { ValidationFilters } from '@/components';

const [filters, setFilters] = useState({});

<ValidationFilters
  filters={filters}
  onFiltersChange={setFilters}
  availableDatasets={datasets}
  availableTypes={types}
  availableStatuses={statuses}
/>
```

### 4. ExportCSVButton

Located in `frontend/src/components/ExportCSVButton.tsx`

Generic CSV export button for validation results.

```tsx
import { ExportCSVButton } from '@/components';

<ExportCSVButton
  data={validationHistory}
  filename="validation_results.csv"
  headers={[
    { key: 'id', label: 'ID' },
    { key: 'dataset_name', label: 'Dataset' },
    { key: 'validation_type', label: 'Type' },
    { key: 'status', label: 'Status' },
    { key: 'pass_rate', label: 'Pass Rate' }
  ]}
/>
```

## Database Setup

### Running Migrations

1. Ensure PostgreSQL is running
2. Apply migrations:

```bash
cd backend
alembic upgrade head
```

This will create:
- `validation_logs` table
- `schema_contracts` table

### Migration Files

- `001_validation_logs.py`: Creates validation_logs table with indexes
- `002_schema_contracts.py`: Creates schema_contracts table with indexes

## Testing

### Running the Validation System Test

```bash
cd backend
python test_validation_system.py
```

This test script:
1. Creates a test DataFrame
2. Sets up validation aggregator with multiple validators
3. Executes validation
4. Logs results to PostgreSQL
5. Retrieves and displays metrics, history, and statistics

### Expected Output

The test will display:
- Validation summary with overall status
- Individual validator results
- Validation history from database
- Validation metrics
- Dataset statistics

## API Integration Examples

### Example: Validate and Log Dataset

```python
from pyspark.sql import SparkSession
from app.validators import ValidationAggregator
from app.services.validation_log_service import ValidationLogService
from app.core.database import SessionLocal

# Initialize Spark
spark = SparkSession.builder.appName("Validation").getOrCreate()

# Load dataset
df = spark.read.csv("s3://bucket/customers.csv", header=True, inferSchema=True)

# Create aggregator with default validators
aggregator = ValidationAggregator()
summary = aggregator.validate_with_defaults(
    df, 
    dataset_name="customers",
    schema_contract={
        'columns': [
            {'name': 'id', 'type': 'integer', 'required': True},
            {'name': 'name', 'type': 'string', 'required': True},
            {'name': 'email', 'type': 'string', 'required': True}
        ]
    },
    null_threshold=5.0
)

# Log to database
db = SessionLocal()
log_service = ValidationLogService(db)
log_service.log_validation_summary(summary)
db.close()

# Check if validation passed
if summary.overall_passed:
    print("✓ All validations passed!")
else:
    print(f"✗ Validation failed: {summary.overall_status}")
```

### Example: Retrieve Validation Metrics for Dashboard

```python
from app.services.validation_log_service import ValidationLogService
from app.core.database import SessionLocal

db = SessionLocal()
log_service = ValidationLogService(db)

# Get metrics for last 30 days
metrics = log_service.get_validation_metrics(days=30)

# Get dataset-specific metrics
customer_metrics = log_service.get_validation_metrics(
    dataset_name="customers",
    days=30
)

# Get statistics for a dataset
stats = log_service.get_dataset_statistics("customers")

db.close()
```

## Configuration

### Validation Thresholds

Configure validation thresholds in your application:

```python
# Null validation threshold
null_threshold = 5.0  # Maximum 5% nulls allowed

# Pass rate threshold for warnings
warning_threshold = 95.0  # Warn if pass rate < 95%

# Pass rate threshold for failures
failure_threshold = 90.0  # Fail if pass rate < 90%
```

### Database Connection

Configure database connection in `backend/app/core/config.py`:

```python
DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"
```

## Best Practices

1. **Use Validation Aggregator**: Always use `ValidationAggregator` to combine multiple validators
2. **Log All Validations**: Always log validation results for tracking and auditing
3. **Set Appropriate Thresholds**: Configure null and pass rate thresholds based on your data quality requirements
4. **Monitor Trends**: Use validation metrics to monitor data quality trends over time
5. **Handle Failures Gracefully**: Check `summary.overall_passed` before proceeding with data processing
6. **Clean Old Logs**: Periodically clean old validation logs using `log_service.delete_old_logs(days=90)`

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:
1. Verify PostgreSQL is running
2. Check database credentials in config
3. Ensure database exists
4. Run migrations: `alembic upgrade head`

### Validation Errors

If validators fail unexpectedly:
1. Check the `errors` field in ValidationResult
2. Review the `details` field for specific issues
3. Verify DataFrame schema matches expectations
4. Check for null values in non-nullable columns

### Performance Issues

For large datasets:
1. Use sampling for validation
2. Increase Spark executor memory
3. Partition data appropriately
4. Consider running validations in parallel

## Future Enhancements

The following features are planned but NOT yet implemented:
- Great Expectations integration
- Airflow integration for scheduled validations
- AWS Glue integration
- Redis caching for validation results
- Celery tasks for async validation
- Schema drift detection
- Real-time validation alerts
- Advanced anomaly detection

## Support

For issues or questions, please contact the development team or file an issue in the project repository.
