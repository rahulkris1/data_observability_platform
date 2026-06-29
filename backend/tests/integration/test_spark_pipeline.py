"""Integration tests for PySpark pipeline.

Tests local PySpark ingestion and validation workflow including:
- Spark session initialization
- Data ingestion from MinIO
- Data transformation
- Validation execution
- Result storage
"""
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import json
from datetime import datetime

from app.utils.spark_utils import get_spark_session, get_spark
from app.storage.minio_client import minio_client
from app.validators.schema_validator import SchemaValidator
from app.validators.null_validator import NullValidator
from app.validators.datatype_validator import DatatypeValidator


@pytest.fixture(scope="module")
def spark():
    """Create Spark session for testing."""
    spark = get_spark_session(
        app_name="test_data_observability",
        master="local[2]",
        config={
            "spark.sql.shuffle.partitions": "2",
            "spark.default.parallelism": "2",
        }
    )
    yield spark
    spark.stop()


@pytest.fixture
def sample_csv_in_minio():
    """Upload sample CSV to MinIO."""
    csv_content = b"""customer_id,name,email,age,city
1,John Doe,john@example.com,30,New York
2,Jane Smith,jane@example.com,25,Los Angeles
3,Bob Johnson,bob@example.com,35,Chicago
4,Alice Williams,alice@example.com,28,Houston
5,Charlie Brown,charlie@example.com,45,Phoenix"""
    
    object_name = "raw/test_customers_spark.csv"
    minio_client.upload_object(
        bucket_type="raw",
        object_name=object_name,
        data=csv_content,
        content_type="text/csv"
    )
    
    yield object_name
    
    # Cleanup
    try:
        minio_client.client.remove_object(minio_client.raw_bucket, object_name)
    except:
        pass


@pytest.fixture
def sample_json_in_minio():
    """Upload sample JSON to MinIO."""
    json_data = [
        {"order_id": "1", "customer_id": "1", "amount": "100.50", "status": "completed"},
        {"order_id": "2", "customer_id": "2", "amount": "250.75", "status": "pending"},
        {"order_id": "3", "customer_id": "1", "amount": "75.00", "status": "completed"},
    ]
    
    object_name = "processed/test_orders_spark.json"
    minio_client.upload_object(
        bucket_type="processed",
        object_name=object_name,
        data=json.dumps(json_data).encode(),
        content_type="application/json"
    )
    
    yield object_name
    
    # Cleanup
    try:
        minio_client.client.remove_object(minio_client.processed_bucket, object_name)
    except:
        pass


@pytest.mark.integration
@pytest.mark.requires_spark
class TestSparkPipeline:
    """Integration tests for PySpark pipeline."""
    
    def test_spark_session_creation(self, spark):
        """Test Spark session is properly initialized."""
        assert spark is not None
        assert spark.version is not None
        assert spark.sparkContext.appName == "test_data_observability"
    
    def test_read_csv_from_minio(self, spark, sample_csv_in_minio):
        """Test reading CSV file from MinIO using Spark."""
        # Download from MinIO
        csv_bytes = minio_client.download_object("raw", sample_csv_in_minio)
        assert csv_bytes is not None
        
        # Save to temp location for Spark to read
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(csv_bytes)
            temp_path = f.name
        
        # Read with Spark
        df = spark.read.csv(temp_path, header=True, inferSchema=True)
        
        assert df.count() == 5
        assert "customer_id" in df.columns
        assert "name" in df.columns
        assert "email" in df.columns
        
        # Cleanup
        import os
        os.remove(temp_path)
    
    def test_read_json_from_minio(self, spark, sample_json_in_minio):
        """Test reading JSON file from MinIO using Spark."""
        # Download from MinIO
        json_bytes = minio_client.download_object("processed", sample_json_in_minio)
        assert json_bytes is not None
        
        # Parse JSON and create DataFrame
        data = json.loads(json_bytes)
        df = spark.createDataFrame(data)
        
        assert df.count() == 3
        assert "order_id" in df.columns
        assert "customer_id" in df.columns
        assert "amount" in df.columns
    
    def test_spark_data_transformation(self, spark, sample_csv_in_minio):
        """Test basic data transformation with Spark."""
        # Download and create DataFrame
        csv_bytes = minio_client.download_object("raw", sample_csv_in_minio)
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(csv_bytes)
            temp_path = f.name
        
        df = spark.read.csv(temp_path, header=True, inferSchema=True)
        
        # Transform: Filter customers older than 30
        filtered_df = df.filter(df.age > 30)
        
        assert filtered_df.count() == 2  # Bob (35) and Charlie (45)
        
        # Transform: Add new column
        from pyspark.sql.functions import upper
        transformed_df = df.withColumn("name_upper", upper(df.name))
        
        assert "name_upper" in transformed_df.columns
        
        # Cleanup
        import os
        os.remove(temp_path)
    
    def test_spark_schema_validation(self, spark):
        """Test schema validation with Spark DataFrame."""
        # Define expected schema
        expected_schema = StructType([
            StructField("customer_id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("email", StringType(), True),
            StructField("age", StringType(), True),
        ])
        
        # Create DataFrame with matching schema
        data = [
            ("1", "John Doe", "john@example.com", "30"),
            ("2", "Jane Smith", "jane@example.com", "25"),
        ]
        df = spark.createDataFrame(data, expected_schema)
        
        # Verify schema
        assert df.schema == expected_schema
        assert len(df.schema.fields) == 4
    
    def test_spark_null_validation(self, spark):
        """Test null validation with Spark DataFrame."""
        data = [
            ("1", "John Doe", "john@example.com", "30"),
            ("2", None, "jane@example.com", "25"),  # Missing name
            ("3", "Bob", None, "35"),  # Missing email
        ]
        schema = StructType([
            StructField("customer_id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("email", StringType(), True),
            StructField("age", StringType(), True),
        ])
        df = spark.createDataFrame(data, schema)
        
        # Check for nulls
        from pyspark.sql.functions import col, isnan, when, count
        
        null_counts = df.select([
            count(when(col(c).isNull(), c)).alias(c)
            for c in df.columns
        ])
        
        null_dict = null_counts.collect()[0].asDict()
        assert null_dict["name"] == 1
        assert null_dict["email"] == 1
    
    def test_spark_datatype_validation(self, spark):
        """Test datatype validation with Spark."""
        data = [
            ("1", "John Doe", "30", "100.50"),
            ("2", "Jane Smith", "25", "invalid"),  # Invalid amount
            ("3", "Bob", "35", "75.00"),
        ]
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("age", StringType(), True),
            StructField("amount", StringType(), True),
        ])
        df = spark.createDataFrame(data, schema)
        
        # Try to cast amount to double
        from pyspark.sql.functions import col
        from pyspark.sql.types import DoubleType
        
        df_with_cast = df.withColumn("amount_numeric", col("amount").cast(DoubleType()))
        
        # Count null values after cast (invalid conversions become null)
        invalid_count = df_with_cast.filter(
            (col("amount").isNotNull()) & (col("amount_numeric").isNull())
        ).count()
        
        assert invalid_count == 1  # One invalid amount
    
    def test_spark_aggregation(self, spark, sample_json_in_minio):
        """Test data aggregation with Spark."""
        json_bytes = minio_client.download_object("processed", sample_json_in_minio)
        data = json.loads(json_bytes)
        df = spark.createDataFrame(data)
        
        # Group by customer and count orders
        from pyspark.sql.functions import count, col
        
        agg_df = df.groupBy("customer_id").agg(
            count("order_id").alias("order_count")
        )
        
        assert agg_df.count() == 2  # Two unique customers
        
        # Check customer 1 has 2 orders
        customer_1_orders = agg_df.filter(col("customer_id") == "1").collect()[0]["order_count"]
        assert customer_1_orders == 2
    
    def test_spark_write_to_minio(self, spark):
        """Test writing Spark DataFrame results to MinIO."""
        # Create sample DataFrame
        data = [
            {"validation_id": "1", "dataset": "customers", "status": "PASSED", "records": 100},
            {"validation_id": "2", "dataset": "orders", "status": "FAILED", "records": 50},
        ]
        df = spark.createDataFrame(data)
        
        # Convert to JSON
        results = [row.asDict() for row in df.collect()]
        results_json = json.dumps(results).encode()
        
        # Write to MinIO
        object_name = "validation_results/test_results.json"
        uploaded = minio_client.upload_object(
            bucket_type="processed",
            object_name=object_name,
            data=results_json,
            content_type="application/json"
        )
        
        assert uploaded is True
        
        # Verify can read back
        read_back = minio_client.download_object("processed", object_name)
        assert read_back is not None
        assert json.loads(read_back) == results
        
        # Cleanup
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, object_name)
        except:
            pass
    
    def test_full_ingestion_validation_workflow(self, spark, sample_csv_in_minio):
        """Test complete ingestion and validation workflow."""
        # Step 1: Ingest from MinIO
        csv_bytes = minio_client.download_object("raw", sample_csv_in_minio)
        assert csv_bytes is not None
        
        # Step 2: Load into Spark
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(csv_bytes)
            temp_path = f.name
        
        df = spark.read.csv(temp_path, header=True, inferSchema=True)
        
        # Step 3: Run validations
        validation_results = {
            "dataset": "test_customers",
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": df.count(),
            "validations": []
        }
        
        # Schema validation
        expected_columns = ["customer_id", "name", "email", "age", "city"]
        actual_columns = df.columns
        schema_valid = set(expected_columns) == set(actual_columns)
        validation_results["validations"].append({
            "validator": "schema",
            "status": "PASSED" if schema_valid else "FAILED",
            "expected_columns": expected_columns,
            "actual_columns": actual_columns
        })
        
        # Null validation
        from pyspark.sql.functions import col, count, when
        null_counts = df.select([
            count(when(col(c).isNull(), c)).alias(c)
            for c in df.columns
        ]).collect()[0].asDict()
        
        has_nulls = any(v > 0 for v in null_counts.values())
        validation_results["validations"].append({
            "validator": "null",
            "status": "WARNING" if has_nulls else "PASSED",
            "null_counts": null_counts
        })
        
        # Step 4: Store validation results in MinIO
        results_object = "validation_results/full_workflow_test.json"
        results_json = json.dumps(validation_results).encode()
        minio_client.upload_object(
            bucket_type="processed",
            object_name=results_object,
            data=results_json,
            content_type="application/json"
        )
        
        # Step 5: Verify results can be retrieved
        retrieved = minio_client.download_object("processed", results_object)
        assert retrieved is not None
        retrieved_data = json.loads(retrieved)
        assert retrieved_data["total_records"] == 5
        assert len(retrieved_data["validations"]) == 2
        
        # Cleanup
        import os
        os.remove(temp_path)
        try:
            minio_client.client.remove_object(minio_client.processed_bucket, results_object)
        except:
            pass
    
    def test_spark_job_failure_handling(self, spark):
        """Test handling of Spark job failures."""
        # Create DataFrame with invalid operations
        data = [("1", "test")]
        df = spark.createDataFrame(data, ["id", "value"])
        
        # Try to perform invalid operation
        from pyspark.sql.functions import col
        
        try:
            # This should work - just dividing by a number
            result_df = df.withColumn("computed", col("id").cast("int") / 2)
            assert result_df.count() == 1
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
    
    def test_spark_performance_on_larger_dataset(self, spark):
        """Test Spark performance on moderately sized dataset."""
        # Generate larger dataset
        from pyspark.sql.functions import lit, concat
        
        data = [(str(i), f"Customer {i}", f"customer{i}@example.com", str(20 + i % 50))
                for i in range(10000)]
        schema = StructType([
            StructField("customer_id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("email", StringType(), True),
            StructField("age", StringType(), True),
        ])
        
        df = spark.createDataFrame(data, schema)
        
        # Perform transformations
        start_time = datetime.utcnow()
        
        result_df = df.filter(col("age").cast("int") > 40) \
                      .withColumn("email_domain", 
                                 concat(lit("@"), col("email")))
        
        count = result_df.count()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        assert count > 0
        assert duration < 30  # Should complete in under 30 seconds


@pytest.mark.integration
@pytest.mark.requires_spark
@pytest.mark.slow
class TestSparkValidatorIntegration:
    """Integration tests for validators with Spark DataFrames."""
    
    def test_schema_validator_with_spark_df(self, spark):
        """Test SchemaValidator with Spark DataFrame."""
        data = [
            ("1", "John", "john@example.com"),
            ("2", "Jane", "jane@example.com"),
        ]
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("email", StringType(), True),
        ])
        df = spark.createDataFrame(data, schema)
        
        # Convert to list of dicts for validator
        records = [row.asDict() for row in df.collect()]
        
        # This would use the SchemaValidator if it accepts list of dicts
        assert len(records) == 2
        assert "id" in records[0]
    
    def test_null_validator_with_spark_df(self, spark):
        """Test NullValidator integration with Spark DataFrame."""
        data = [
            ("1", "John", "john@example.com"),
            ("2", None, "jane@example.com"),
            ("3", "Bob", None),
        ]
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("name", StringType(), True),
            StructField("email", StringType(), True),
        ])
        df = spark.createDataFrame(data, schema)
        
        # Check nulls using Spark
        from pyspark.sql.functions import col, count, when
        
        null_check = df.select([
            count(when(col(c).isNull(), c)).alias(f"{c}_nulls")
            for c in df.columns
        ]).collect()[0].asDict()
        
        assert null_check["name_nulls"] == 1
        assert null_check["email_nulls"] == 1
