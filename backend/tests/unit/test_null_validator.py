"""Unit tests for NullValidator."""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from app.validators.null_validator import NullValidator
from app.validators.base_validator import ValidationStatus


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("NullValidatorTests") \
        .master("local[1]") \
        .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse") \
        .config("spark.driver.host", "localhost") \
        .getOrCreate()
    
    yield spark
    spark.stop()


@pytest.fixture
def dataframe_no_nulls(spark):
    """Create DataFrame without null values."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("email", StringType(), False)
    ])
    data = [
        (1, "Alice", "alice@example.com"),
        (2, "Bob", "bob@example.com"),
        (3, "Charlie", "charlie@example.com")
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_with_nulls(spark):
    """Create DataFrame with some null values."""
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True)
    ])
    data = [
        (1, "Alice", "alice@example.com", "555-0001"),
        (2, "Bob", None, "555-0002"),  # Null email
        (3, "Charlie", "charlie@example.com", None),  # Null phone
        (4, None, "dan@example.com", None),  # Null name and phone
        (5, "Eve", None, None)  # Null email and phone
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_completely_null_column(spark):
    """Create DataFrame with one completely null column."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("empty_field", StringType(), True)
    ])
    data = [
        (1, "Alice", None),
        (2, "Bob", None),
        (3, "Charlie", None)
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_high_null_percentage(spark):
    """Create DataFrame with high null percentage."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("optional_field", StringType(), True)
    ])
    data = [
        (1, "value"),
        (2, None),
        (3, None),
        (4, None),
        (5, None),
        (6, None),
        (7, None),
        (8, None),
        (9, None),
        (10, None)  # 90% null
    ]
    return spark.createDataFrame(data, schema=schema)


class TestNullValidatorBasicFunctionality:
    """Test basic null validation functionality."""
    
    def test_no_nulls_passes(self, dataframe_no_nulls):
        """Test that DataFrame without nulls passes validation."""
        validator = NullValidator(
            non_null_columns=["id", "name", "email"]
        )
        
        result = validator.validate(dataframe_no_nulls)
        
        assert result.passed is True
        assert result.status == ValidationStatus.PASSED
        assert result.validator_name == "NullValidator"
        assert len(result.errors) == 0
        assert "null_counts" in result.details
        assert "null_percentages" in result.details
        assert result.details["overall_null_percentage"] == 0.0
    
    def test_null_in_non_null_column_fails(self, dataframe_with_nulls):
        """Test that nulls in non-null columns cause validation to fail."""
        validator = NullValidator(
            non_null_columns=["id", "name", "email"]
        )
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is False
        assert result.status == ValidationStatus.FAILED
        assert len(result.errors) > 0
        
        # Check that errors mention the columns with nulls
        error_text = " ".join(result.errors).lower()
        assert "name" in error_text or "email" in error_text
        assert "must not contain nulls" in error_text
    
    def test_null_counts_calculated_correctly(self, dataframe_with_nulls):
        """Test that null counts are calculated correctly."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_with_nulls)
        
        null_counts = result.details["null_counts"]
        assert null_counts["id"] == 1
        assert null_counts["name"] == 1
        assert null_counts["email"] == 2
        assert null_counts["phone"] == 3
    
    def test_null_percentages_calculated_correctly(self, dataframe_with_nulls):
        """Test that null percentages are calculated correctly."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_with_nulls)
        
        null_percentages = result.details["null_percentages"]
        assert null_percentages["id"] == 20.0  # 1/5 = 20%
        assert null_percentages["name"] == 20.0
        assert null_percentages["email"] == 40.0  # 2/5 = 40%
        assert null_percentages["phone"] == 60.0  # 3/5 = 60%


class TestNullValidatorThresholds:
    """Test null threshold validation."""
    
    def test_column_threshold_pass(self, dataframe_with_nulls):
        """Test that validation passes when within column threshold."""
        validator = NullValidator(
            column_thresholds={
                "email": 50.0,  # 40% actual, passes
                "phone": 70.0   # 60% actual, passes
            }
        )
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is True
    
    def test_column_threshold_fail(self, dataframe_with_nulls):
        """Test that validation fails when exceeding column threshold."""
        validator = NullValidator(
            column_thresholds={
                "email": 30.0,  # 40% actual, fails
                "phone": 50.0   # 60% actual, fails
            }
        )
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is False
        assert len(result.errors) >= 2
        
        error_text = " ".join(result.errors)
        assert "email" in error_text.lower()
        assert "phone" in error_text.lower()
        assert "exceeds null threshold" in error_text.lower()
    
    def test_global_max_null_percentage(self, dataframe_high_null_percentage):
        """Test global max null percentage threshold."""
        validator = NullValidator(max_null_percentage=10.0)
        
        result = validator.validate(dataframe_high_null_percentage)
        
        assert result.passed is False
        assert len(result.errors) > 0
        assert "exceeds global null threshold" in result.errors[0].lower()
    
    def test_global_max_null_percentage_pass(self, dataframe_with_nulls):
        """Test that validation passes when under global threshold."""
        validator = NullValidator(max_null_percentage=70.0)
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is True


class TestNullValidatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self, spark):
        """Test validation with empty DataFrame."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("name", StringType(), False)
        ])
        empty_df = spark.createDataFrame([], schema=schema)
        
        validator = NullValidator(non_null_columns=["id", "name"])
        
        result = validator.validate(empty_df)
        
        assert result.status == ValidationStatus.WARNING
        assert result.passed is False
        assert "empty" in result.message.lower()
    
    def test_completely_null_column_detected(self, dataframe_completely_null_column):
        """Test that completely null columns are detected."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_completely_null_column)
        
        assert "empty_columns" in result.details
        assert "empty_field" in result.details["empty_columns"]
        assert any("completely empty column" in err.lower() for err in result.errors)
    
    def test_specific_columns_check(self, dataframe_with_nulls):
        """Test validation with specific columns specified via kwargs."""
        validator = NullValidator(non_null_columns=["id"])
        
        result = validator.validate(dataframe_with_nulls, columns=["id", "name"])
        
        # Should only check id and name, not email or phone
        assert "id" in result.details["null_counts"]
        assert "name" in result.details["null_counts"]
        assert result.details["columns_checked"] == 2
    
    def test_nonexistent_column(self, dataframe_no_nulls):
        """Test validation with nonexistent column."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_no_nulls, columns=["id", "nonexistent_column"])
        
        assert any("not found" in err.lower() for err in result.errors)
    
    def test_overall_null_statistics(self, dataframe_with_nulls):
        """Test that overall null statistics are calculated."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_with_nulls)
        
        assert "total_null_values" in result.details
        assert "overall_null_percentage" in result.details
        assert "total_records" in result.details
        
        # 1 + 1 + 2 + 3 = 7 nulls, 5 rows * 4 columns = 20 cells
        assert result.details["total_null_values"] == 7
        assert result.details["overall_null_percentage"] == 35.0  # 7/20 = 35%


class TestNullValidatorMultipleConstraints:
    """Test multiple constraints simultaneously."""
    
    def test_combined_constraints(self, dataframe_with_nulls):
        """Test multiple constraints applied together."""
        validator = NullValidator(
            non_null_columns=["id"],
            max_null_percentage=50.0,
            column_thresholds={"email": 35.0}
        )
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is False
        # Should fail on both id (has 1 null) and email (40% > 35%)
        error_text = " ".join(result.errors).lower()
        assert "id" in error_text and "must not contain nulls" in error_text
        assert "email" in error_text and "exceeds null threshold" in error_text


class TestNullValidatorExecutionMetrics:
    """Test execution metrics and performance tracking."""
    
    def test_execution_time_recorded(self, dataframe_no_nulls):
        """Test that execution time is recorded."""
        validator = NullValidator(non_null_columns=["id"])
        
        result = validator.validate(dataframe_no_nulls)
        
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
    
    def test_failed_records_count(self, dataframe_with_nulls):
        """Test that failed records count equals total null values."""
        validator = NullValidator()
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.failed_records == result.details["total_null_values"]
    
    def test_custom_validator_name(self, dataframe_no_nulls):
        """Test custom validator name."""
        custom_name = "CustomNullChecker"
        validator = NullValidator(name=custom_name)
        
        result = validator.validate(dataframe_no_nulls)
        
        assert result.validator_name == custom_name
