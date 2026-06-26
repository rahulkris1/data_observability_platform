"""Sample test datasets for unit tests."""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, TimestampType, DateType
)
from datetime import datetime, date


def create_customer_dataset(spark: SparkSession):
    """Create a sample customer dataset."""
    schema = StructType([
        StructField("customer_id", IntegerType(), False),
        StructField("first_name", StringType(), False),
        StructField("last_name", StringType(), False),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("signup_date", DateType(), False),
        StructField("is_active", BooleanType(), False),
        StructField("lifetime_value", DoubleType(), True)
    ])
    
    data = [
        (1, "John", "Doe", "john.doe@example.com", "555-0001", 35, date(2023, 1, 15), True, 1250.50),
        (2, "Jane", "Smith", "jane.smith@example.com", "555-0002", 28, date(2023, 2, 20), True, 890.25),
        (3, "Bob", "Johnson", "bob.j@example.com", None, 42, date(2023, 1, 10), True, 2150.75),
        (4, "Alice", "Williams", None, "555-0004", 31, date(2023, 3, 5), True, 560.00),
        (5, "Charlie", "Brown", "charlie.b@example.com", "555-0005", 25, date(2023, 2, 1), False, 125.50)
    ]
    
    return spark.createDataFrame(data, schema=schema)


def create_order_dataset(spark: SparkSession):
    """Create a sample order dataset."""
    schema = StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", IntegerType(), False),
        StructField("order_date", DateType(), False),
        StructField("total_amount", DoubleType(), False),
        StructField("status", StringType(), False),
        StructField("shipping_address", StringType(), True),
        StructField("discount_applied", DoubleType(), True)
    ])
    
    data = [
        (101, 1, date(2023, 3, 10), 125.50, "delivered", "123 Main St", 10.0),
        (102, 1, date(2023, 3, 15), 75.25, "delivered", "123 Main St", 0.0),
        (103, 2, date(2023, 3, 12), 200.00, "shipped", "456 Oak Ave", 15.0),
        (104, 3, date(2023, 3, 14), 450.75, "processing", None, None),
        (105, 4, date(2023, 3, 16), 89.99, "delivered", "789 Pine Rd", 5.0),
        (106, 2, date(2023, 3, 18), 150.50, "cancelled", "456 Oak Ave", 0.0)
    ]
    
    return spark.createDataFrame(data, schema=schema)


def create_product_dataset(spark: SparkSession):
    """Create a sample product dataset."""
    schema = StructType([
        StructField("product_id", IntegerType(), False),
        StructField("name", StringType(), False),
        StructField("category", StringType(), False),
        StructField("price", DoubleType(), False),
        StructField("stock_quantity", IntegerType(), False),
        StructField("weight_kg", DoubleType(), True),
        StructField("is_available", BooleanType(), False)
    ])
    
    data = [
        (1001, "Laptop", "Electronics", 999.99, 15, 2.5, True),
        (1002, "Mouse", "Electronics", 25.50, 150, 0.1, True),
        (1003, "Desk Chair", "Furniture", 299.99, 30, 12.5, True),
        (1004, "Monitor", "Electronics", 399.99, 25, 5.0, True),
        (1005, "Keyboard", "Electronics", 79.99, 80, 0.8, True),
        (1006, "Desk Lamp", "Furniture", 45.00, 60, 1.2, False)
    ]
    
    return spark.createDataFrame(data, schema=schema)


def create_dataset_with_quality_issues(spark: SparkSession):
    """Create a dataset with various data quality issues for testing."""
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("salary", DoubleType(), True)
    ])
    
    data = [
        (1, "Alice", "alice@example.com", 30, 75000.0),
        (2, None, "bob@example.com", 25, 65000.0),  # Missing name
        (3, "Charlie", None, 35, 85000.0),  # Missing email
        (None, "David", "david@example.com", 28, 70000.0),  # Missing id
        (5, "Eve", "eve@example.com", None, None),  # Missing age and salary
        (1, "Alice", "alice@example.com", 30, 75000.0),  # Duplicate row
        (6, "", "blank@example.com", 40, 90000.0),  # Empty name
        (7, "George", "invalid-email", -5, -50000.0),  # Invalid data
        (8, None, None, None, None)  # All nulls except id
    ]
    
    return spark.createDataFrame(data, schema=schema)


def create_time_series_dataset(spark: SparkSession):
    """Create a time series dataset for testing."""
    schema = StructType([
        StructField("timestamp", TimestampType(), False),
        StructField("sensor_id", StringType(), False),
        StructField("temperature", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("pressure", DoubleType(), True)
    ])
    
    data = [
        (datetime(2023, 3, 20, 10, 0, 0), "SENSOR_01", 22.5, 45.0, 1013.25),
        (datetime(2023, 3, 20, 10, 5, 0), "SENSOR_01", 22.8, 46.5, 1013.20),
        (datetime(2023, 3, 20, 10, 10, 0), "SENSOR_01", None, 47.0, 1013.15),
        (datetime(2023, 3, 20, 10, 0, 0), "SENSOR_02", 21.5, 50.0, 1013.30),
        (datetime(2023, 3, 20, 10, 5, 0), "SENSOR_02", 21.8, None, 1013.25),
        (datetime(2023, 3, 20, 10, 10, 0), "SENSOR_02", 22.0, 51.5, None)
    ]
    
    return spark.createDataFrame(data, schema=schema)


# Schema definitions that can be used for validation tests
CUSTOMER_SCHEMA = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("first_name", StringType(), False),
    StructField("last_name", StringType(), False),
    StructField("email", StringType(), True),
    StructField("phone", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("signup_date", DateType(), False),
    StructField("is_active", BooleanType(), False),
    StructField("lifetime_value", DoubleType(), True)
])

ORDER_SCHEMA = StructType([
    StructField("order_id", IntegerType(), False),
    StructField("customer_id", IntegerType(), False),
    StructField("order_date", DateType(), False),
    StructField("total_amount", DoubleType(), False),
    StructField("status", StringType(), False),
    StructField("shipping_address", StringType(), True),
    StructField("discount_applied", DoubleType(), True)
])

PRODUCT_SCHEMA = StructType([
    StructField("product_id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("category", StringType(), False),
    StructField("price", DoubleType(), False),
    StructField("stock_quantity", IntegerType(), False),
    StructField("weight_kg", DoubleType(), True),
    StructField("is_available", BooleanType(), False)
])
