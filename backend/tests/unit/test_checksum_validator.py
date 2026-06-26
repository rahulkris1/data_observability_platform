"""Unit tests for ChecksumValidator."""

import pytest
import hashlib
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from app.validators.checksum_validator import ChecksumValidator
from app.validators.base_validator import ValidationStatus


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("ChecksumValidatorTests") \
        .master("local[1]") \
        .config("spark.sql.warehouse.dir", "file:///tmp/spark-warehouse") \
        .config("spark.driver.host", "localhost") \
        .getOrCreate()
    
    yield spark
    spark.stop()


@pytest.fixture
def sample_dataframe(spark):
    """Create a sample DataFrame for testing."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("value", IntegerType(), False)
    ])
    data = [
        (1, "Alice", 100),
        (2, "Bob", 200),
        (3, "Charlie", 300)
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_with_duplicates(spark):
    """Create DataFrame with duplicate rows."""
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("value", IntegerType(), False)
    ])
    data = [
        (1, "Alice", 100),
        (2, "Bob", 200),
        (1, "Alice", 100),  # Duplicate
        (3, "Charlie", 300),
        (2, "Bob", 200)  # Duplicate
    ]
    return spark.createDataFrame(data, schema=schema)


@pytest.fixture
def dataframe_with_nulls(spark):
    """Create DataFrame with null values."""
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("value", IntegerType(), True)
    ])
    data = [
        (1, "Alice", 100),
        (2, None, 200),
        (None, "Charlie", None)
    ]
    return spark.createDataFrame(data, schema=schema)


def calculate_expected_checksum(data_rows, columns, algorithm='md5'):
    """
    Helper function to calculate expected dataset checksum.
    
    Args:
        data_rows: List of tuples representing data
        columns: Column names
        algorithm: Hash algorithm
        
    Returns:
        Expected checksum string
    """
    row_checksums = []
    for row in data_rows:
        # Convert row to string, replacing None with "NULL"
        row_str = "|".join([str(v) if v is not None else "NULL" for v in row])
        if algorithm == 'md5':
            row_hash = hashlib.md5(row_str.encode()).hexdigest()
        else:
            row_hash = hashlib.sha256(row_str.encode()).hexdigest()
        row_checksums.append(row_hash)
    
    row_checksums.sort()
    combined = "|".join(row_checksums)
    
    if algorithm == 'md5':
        return hashlib.md5(combined.encode()).hexdigest()
    else:
        return hashlib.sha256(combined.encode()).hexdigest()


class TestChecksumValidatorBasicFunctionality:
    """Test basic checksum validation functionality."""
    
    def test_checksum_calculation_succeeds(self, sample_dataframe):
        """Test that checksum calculation succeeds."""
        validator = ChecksumValidator()
        
        result = validator.validate(sample_dataframe)
        
        assert result.passed is True
        assert result.status == ValidationStatus.PASSED
        assert result.validator_name == "ChecksumValidator"
        assert "dataset_checksum" in result.details
        assert len(result.details["dataset_checksum"]) == 32  # MD5 hash length
    
    def test_checksum_with_expected_value_matches(self, sample_dataframe):
        """Test that checksum matches expected value."""
        # First, get the actual checksum
        validator1 = ChecksumValidator()
        result1 = validator1.validate(sample_dataframe)
        expected_checksum = result1.details["dataset_checksum"]
        
        # Now validate with expected checksum
        validator2 = ChecksumValidator(expected_checksum=expected_checksum)
        result2 = validator2.validate(sample_dataframe)
        
        assert result2.passed is True
        assert result2.details["checksum_match"] is True
        assert result2.details["expected_checksum"] == expected_checksum
    
    def test_checksum_mismatch_detected(self, sample_dataframe):
        """Test that checksum mismatch is detected."""
        incorrect_checksum = "incorrect_checksum_value_123456789"
        validator = ChecksumValidator(expected_checksum=incorrect_checksum)
        
        result = validator.validate(sample_dataframe)
        
        assert result.passed is False
        assert result.status == ValidationStatus.FAILED
        assert result.details["checksum_match"] is False
        assert any("mismatch" in err.lower() for err in result.errors)
    
    def test_column_checksums_calculated(self, sample_dataframe):
        """Test that column-level checksums are calculated."""
        validator = ChecksumValidator()
        
        result = validator.validate(sample_dataframe)
        
        assert "column_checksums" in result.details
        column_checksums = result.details["column_checksums"]
        
        assert "id" in column_checksums
        assert "name" in column_checksums
        assert "value" in column_checksums
        
        # Each column checksum should be a valid MD5 hash
        for col_checksum in column_checksums.values():
            assert len(col_checksum) == 32
            assert all(c in '0123456789abcdef' for c in col_checksum)


class TestChecksumValidatorDuplicateDetection:
    """Test duplicate detection functionality."""
    
    def test_no_duplicates_passes(self, sample_dataframe):
        """Test that DataFrame without duplicates passes."""
        validator = ChecksumValidator(detect_duplicates=True)
        
        result = validator.validate(sample_dataframe)
        
        assert result.passed is True
        assert result.details["duplicate_count"] == 0
    
    def test_duplicates_detected(self, dataframe_with_duplicates):
        """Test that duplicate rows are detected."""
        validator = ChecksumValidator(detect_duplicates=True)
        
        result = validator.validate(dataframe_with_duplicates)
        
        assert result.passed is False
        assert result.status == ValidationStatus.FAILED
        assert result.details["duplicate_count"] > 0
        assert any("duplicate" in err.lower() for err in result.errors)
        
        # Should detect 2 duplicate groups (Alice and Bob each appear twice)
        assert result.details["duplicate_count"] == 2
    
    def test_duplicate_detection_disabled(self, dataframe_with_duplicates):
        """Test that duplicates are not reported when detection is disabled."""
        validator = ChecksumValidator(detect_duplicates=False)
        
        result = validator.validate(dataframe_with_duplicates)
        
        # Should pass as duplicate detection is off
        assert result.passed is True
        assert "duplicate_count" not in result.details


class TestChecksumValidatorColumnSelection:
    """Test checksum calculation with specific columns."""
    
    def test_specific_columns_checksum(self, sample_dataframe):
        """Test checksum calculation with specific columns."""
        validator = ChecksumValidator(checksum_columns=["id", "name"])
        
        result = validator.validate(sample_dataframe)
        
        assert result.passed is True
        assert result.details["checksum_columns"] == ["id", "name"]
        
        # Column checksums should only include specified columns
        column_checksums = result.details["column_checksums"]
        assert "id" in column_checksums
        assert "name" in column_checksums
        assert len(column_checksums) == 2
    
    def test_missing_checksum_columns(self, sample_dataframe):
        """Test validation with nonexistent columns."""
        validator = ChecksumValidator(checksum_columns=["id", "nonexistent_column"])
        
        result = validator.validate(sample_dataframe)
        
        # Should report error but continue with valid columns
        assert any("not found" in err.lower() for err in result.errors)
        assert result.details["checksum_columns"] == ["id"]


class TestChecksumValidatorAlgorithms:
    """Test different hash algorithms."""
    
    def test_md5_algorithm(self, sample_dataframe):
        """Test checksum with MD5 algorithm."""
        validator = ChecksumValidator()
        
        result = validator.validate(sample_dataframe, algorithm='md5')
        
        assert result.passed is True
        assert result.details["checksum_algorithm"] == "md5"
        assert len(result.details["dataset_checksum"]) == 32  # MD5 length
    
    def test_sha256_algorithm(self, sample_dataframe):
        """Test checksum with SHA256 algorithm."""
        validator = ChecksumValidator()
        
        result = validator.validate(sample_dataframe, algorithm='sha256')
        
        assert result.passed is True
        assert result.details["checksum_algorithm"] == "sha256"
        assert len(result.details["dataset_checksum"]) == 64  # SHA256 length
    
    def test_different_algorithms_produce_different_checksums(self, sample_dataframe):
        """Test that different algorithms produce different checksums."""
        validator = ChecksumValidator()
        
        result_md5 = validator.validate(sample_dataframe, algorithm='md5')
        result_sha256 = validator.validate(sample_dataframe, algorithm='sha256')
        
        assert result_md5.details["dataset_checksum"] != result_sha256.details["dataset_checksum"]


class TestChecksumValidatorNullHandling:
    """Test checksum calculation with null values."""
    
    def test_null_values_handled(self, dataframe_with_nulls):
        """Test that null values are handled correctly in checksums."""
        validator = ChecksumValidator()
        
        result = validator.validate(dataframe_with_nulls)
        
        assert result.passed is True
        assert "dataset_checksum" in result.details
        # Nulls should be converted to "NULL" string for consistency
    
    def test_null_values_consistency(self, spark):
        """Test that null values are handled consistently."""
        schema = StructType([
            StructField("id", IntegerType(), True),
            StructField("value", StringType(), True)
        ])
        
        # Create two DataFrames with same null pattern
        data = [(1, None), (None, "test")]
        df1 = spark.createDataFrame(data, schema=schema)
        df2 = spark.createDataFrame(data, schema=schema)
        
        validator = ChecksumValidator()
        result1 = validator.validate(df1)
        result2 = validator.validate(df2)
        
        # Same data should produce same checksum
        assert result1.details["dataset_checksum"] == result2.details["dataset_checksum"]


class TestChecksumValidatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self, spark):
        """Test validation with empty DataFrame."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("name", StringType(), False)
        ])
        empty_df = spark.createDataFrame([], schema=schema)
        
        validator = ChecksumValidator()
        result = validator.validate(empty_df)
        
        assert result.status == ValidationStatus.WARNING
        assert result.passed is False
        assert "empty" in result.message.lower()
    
    def test_single_row_dataframe(self, spark):
        """Test validation with single row DataFrame."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("name", StringType(), False)
        ])
        data = [(1, "Alice")]
        single_row_df = spark.createDataFrame(data, schema=schema)
        
        validator = ChecksumValidator()
        result = validator.validate(single_row_df)
        
        assert result.passed is True
        assert "dataset_checksum" in result.details
    
    def test_no_valid_columns_error(self, sample_dataframe):
        """Test error when no valid columns for checksum."""
        validator = ChecksumValidator(checksum_columns=["nonexistent1", "nonexistent2"])
        
        result = validator.validate(sample_dataframe)
        
        assert result.status == ValidationStatus.ERROR
        assert result.passed is False
        assert "no valid columns" in result.message.lower()


class TestChecksumValidatorExecutionMetrics:
    """Test execution metrics and performance tracking."""
    
    def test_execution_time_recorded(self, sample_dataframe):
        """Test that execution time is recorded."""
        validator = ChecksumValidator()
        
        result = validator.validate(sample_dataframe)
        
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
    
    def test_failed_records_count_with_duplicates(self, dataframe_with_duplicates):
        """Test that failed records equals duplicate count."""
        validator = ChecksumValidator(detect_duplicates=True)
        
        result = validator.validate(dataframe_with_duplicates)
        
        assert result.failed_records == result.details["duplicate_count"]
    
    def test_custom_validator_name(self, sample_dataframe):
        """Test custom validator name."""
        custom_name = "CustomChecksumValidator"
        validator = ChecksumValidator(name=custom_name)
        
        result = validator.validate(sample_dataframe)
        
        assert result.validator_name == custom_name


class TestChecksumValidatorIntegrity:
    """Test data integrity scenarios."""
    
    def test_data_modification_detected(self, spark):
        """Test that data modification results in different checksum."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("value", IntegerType(), False)
        ])
        
        data1 = [(1, 100), (2, 200), (3, 300)]
        data2 = [(1, 100), (2, 201), (3, 300)]  # One value changed
        
        df1 = spark.createDataFrame(data1, schema=schema)
        df2 = spark.createDataFrame(data2, schema=schema)
        
        validator = ChecksumValidator()
        result1 = validator.validate(df1)
        result2 = validator.validate(df2)
        
        assert result1.details["dataset_checksum"] != result2.details["dataset_checksum"]
    
    def test_row_order_independence(self, spark):
        """Test that checksum is independent of row order."""
        schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("value", IntegerType(), False)
        ])
        
        data1 = [(1, 100), (2, 200), (3, 300)]
        data2 = [(3, 300), (1, 100), (2, 200)]  # Different order
        
        df1 = spark.createDataFrame(data1, schema=schema)
        df2 = spark.createDataFrame(data2, schema=schema)
        
        validator = ChecksumValidator()
        result1 = validator.validate(df1)
        result2 = validator.validate(df2)
        
        # Checksums should be the same regardless of row order
        assert result1.details["dataset_checksum"] == result2.details["dataset_checksum"]
