"""Unit tests for SchemaValidator."""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType
from app.validators.schema_validator import SchemaValidator
from app.validators.base_validator import ValidationStatus


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("SchemaValidatorTests") \
        .master("local[1]") \
        .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse") \
        .config("spark.driver.host", "localhost") \
        .getOrCreate()
    
    yield spark
    spark.stop()


@pytest.fixture
def sample_schema():
    """Define expected schema for testing."""
    return StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("age", IntegerType(), True),
        StructField("email", StringType(), True),
        StructField("is_active", BooleanType(), True)
    ])


@pytest.fixture
def valid_dataframe(spark, sample_schema):
    """Create a valid DataFrame matching expected schema."""
    data = [
        (1, "Alice", 30, "alice@example.com", True),
        (2, "Bob", 25, "bob@example.com", True),
        (3, "Charlie", 35, "charlie@example.com", False)
    ]
    return spark.createDataFrame(data, schema=sample_schema)


@pytest.fixture
def dataframe_with_missing_columns(spark):
    """Create DataFrame with missing required columns."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False)
    ])
    data = [(1, "Alice"), (2, "Bob")]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_with_extra_columns(spark, sample_schema):
    """Create DataFrame with extra columns."""
    schema = StructType(sample_schema.fields + [
        StructField("extra_field", StringType(), True),
        StructField("another_extra", DoubleType(), True)
    ])
    data = [
        (1, "Alice", 30, "alice@example.com", True, "extra_data", 1.5),
        (2, "Bob", 25, "bob@example.com", True, "more_data", 2.5)
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_with_wrong_types(spark):
    """Create DataFrame with incorrect column types."""
    schema = StructType([
        StructField("id", StringType(), False),  # Should be IntegerType
        StructField("name", StringType(), False),
        StructField("age", StringType(), True),  # Should be IntegerType
        StructField("email", StringType(), True),
        StructField("is_active", StringType(), True)  # Should be BooleanType
    ])
    data = [
        ("1", "Alice", "30", "alice@example.com", "true"),
        ("2", "Bob", "25", "bob@example.com", "false")
    ]
    return spark.createDataFrame(data, schema=schema)


class TestSchemaValidatorBasicFunctionality:
    """Test basic schema validation functionality."""
    
    def test_valid_schema_passes(self, valid_dataframe, sample_schema):
        """Test that a valid schema passes validation."""
        validator = SchemaValidator(
            expected_schema=sample_schema,
            required_columns=["id", "name"],
            column_types={"id": "int", "name": "string", "age": "int"}
        )
        
        result = validator.validate(valid_dataframe)
        
        assert result.passed is True
        assert result.status == ValidationStatus.PASSED
        assert result.validator_name == "SchemaValidator"
        assert "passed" in result.message.lower()
        assert len(result.errors) == 0
        assert "actual_columns" in result.details
        assert "column_count" in result.details
    
    def test_missing_required_columns_fails(self, dataframe_with_missing_columns):
        """Test that missing required columns cause validation to fail."""
        validator = SchemaValidator(
            required_columns=["id", "name", "age", "email"]
        )
        
        result = validator.validate(dataframe_with_missing_columns)
        
        assert result.passed is False
        assert result.status == ValidationStatus.FAILED
        assert len(result.errors) > 0
        assert any("missing required columns" in err.lower() for err in result.errors)
        assert "age" in result.errors[0] or "email" in result.errors[0]
    
    def test_extra_columns_detected(self, dataframe_with_extra_columns, sample_schema):
        """Test that extra columns are detected when expected schema is provided."""
        validator = SchemaValidator(expected_schema=sample_schema)
        
        result = validator.validate(dataframe_with_extra_columns)
        
        assert "extra_columns" in result.details
        assert "extra_field" in result.details["extra_columns"]
        assert "another_extra" in result.details["extra_columns"]
    
    def test_type_mismatches_detected(self, dataframe_with_wrong_types):
        """Test that column type mismatches are detected."""
        validator = SchemaValidator(
            column_types={
                "id": "int",
                "age": "int",
                "is_active": "boolean"
            }
        )
        
        result = validator.validate(dataframe_with_wrong_types)
        
        assert result.passed is False
        assert result.status == ValidationStatus.FAILED
        assert "type_mismatches" in result.details
        assert len(result.details["type_mismatches"]) == 3
        
        # Verify specific type mismatches
        type_mismatches = {tm["column"]: tm for tm in result.details["type_mismatches"]}
        assert "id" in type_mismatches
        assert type_mismatches["id"]["expected"] == "int"
        assert type_mismatches["id"]["actual"] == "string"


class TestSchemaValidatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self, spark, sample_schema):
        """Test validation with empty DataFrame."""
        empty_df = spark.createDataFrame([], schema=sample_schema)
        validator = SchemaValidator(
            expected_schema=sample_schema,
            required_columns=["id", "name"]
        )
        
        result = validator.validate(empty_df)
        
        # Schema validation should pass even with empty DataFrame
        assert result.passed is True
        assert result.total_records == 0
        assert result.details["column_count"] == 5
    
    def test_no_validation_criteria(self, valid_dataframe):
        """Test validator with no validation criteria."""
        validator = SchemaValidator()
        
        result = validator.validate(valid_dataframe)
        
        # Should pass as there are no constraints
        assert result.passed is True
        assert "actual_columns" in result.details
    
    def test_partial_column_type_validation(self, valid_dataframe):
        """Test validation with only some column types specified."""
        validator = SchemaValidator(
            column_types={"id": "int", "name": "string"}
        )
        
        result = validator.validate(valid_dataframe)
        
        assert result.passed is True
        assert len(result.errors) == 0
    
    def test_schema_details_included(self, valid_dataframe):
        """Test that schema details are included in validation result."""
        validator = SchemaValidator(required_columns=["id", "name"])
        
        result = validator.validate(valid_dataframe)
        
        assert "schema" in result.details
        assert isinstance(result.details["schema"], dict)
        assert "id" in result.details["schema"]
        assert "name" in result.details["schema"]
        assert result.details["schema"]["id"] == "int"
        assert result.details["schema"]["name"] == "string"
    
    def test_validator_name_customization(self, valid_dataframe):
        """Test custom validator name."""
        custom_name = "CustomSchemaValidator"
        validator = SchemaValidator(
            required_columns=["id"],
            name=custom_name
        )
        
        result = validator.validate(valid_dataframe)
        
        assert result.validator_name == custom_name


class TestSchemaValidatorMultipleErrors:
    """Test scenarios with multiple validation errors."""
    
    def test_multiple_errors_combined(self, spark):
        """Test that multiple errors are all reported."""
        # Create DataFrame with both missing columns and wrong types
        schema = StructType([
            StructField("id", StringType(), False),  # Wrong type
            StructField("name", StringType(), False)
            # Missing: age, email
        ])
        data = [("1", "Alice"), ("2", "Bob")]
        df = spark.createDataFrame(data, schema=schema)
        
        validator = SchemaValidator(
            required_columns=["id", "name", "age", "email"],
            column_types={"id": "int"}
        )
        
        result = validator.validate(df)
        
        assert result.passed is False
        assert len(result.errors) >= 2  # At least missing columns and type mismatch
        
        error_text = " ".join(result.errors)
        assert "missing" in error_text.lower()
        assert "type mismatch" in error_text.lower()


class TestSchemaValidatorExecutionMetrics:
    """Test execution metrics and performance tracking."""
    
    def test_execution_time_recorded(self, valid_dataframe):
        """Test that execution time is recorded."""
        validator = SchemaValidator(required_columns=["id", "name"])
        
        result = validator.validate(valid_dataframe)
        
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
        assert isinstance(result.execution_time_ms, float)
    
    def test_timestamp_recorded(self, valid_dataframe):
        """Test that timestamp is recorded."""
        validator = SchemaValidator(required_columns=["id"])
        
        result = validator.validate(valid_dataframe)
        
        assert result.timestamp is not None
        assert hasattr(result.timestamp, 'isoformat')
