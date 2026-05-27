"""Verify SparkSession startup and local configuration."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.spark_utils import get_spark, SparkSessionManager


def verify_spark_session():
    """Verify SparkSession can be created and configured properly."""
    
    print("=" * 60)
    print("SparkSession Startup Verification")
    print("=" * 60)
    
    try:
        # Get SparkSession
        print("\n1. Creating SparkSession...")
        spark = get_spark()
        
        print(f"   ✓ SparkSession created successfully")
        print(f"   ✓ Spark Version: {spark.version}")
        print(f"   ✓ Master: {spark.sparkContext.master}")
        print(f"   ✓ App Name: {spark.sparkContext.appName}")
        
        # Verify configuration
        print("\n2. Verifying Spark Configuration...")
        configs = {
            "spark.driver.memory": spark.sparkContext.getConf().get("spark.driver.memory"),
            "spark.executor.memory": spark.sparkContext.getConf().get("spark.executor.memory"),
            "spark.sql.adaptive.enabled": spark.sparkContext.getConf().get("spark.sql.adaptive.enabled"),
            "spark.serializer": spark.sparkContext.getConf().get("spark.serializer"),
        }
        
        for key, value in configs.items():
            print(f"   ✓ {key}: {value}")
        
        # Test basic DataFrame operations
        print("\n3. Testing basic DataFrame operations...")
        test_data = [
            ("Alice", 25, "Engineering"),
            ("Bob", 30, "Sales"),
            ("Charlie", 35, "Marketing"),
        ]
        
        df = spark.createDataFrame(test_data, ["name", "age", "department"])
        
        print(f"   ✓ Created test DataFrame with {df.count()} rows")
        print(f"   ✓ Columns: {df.columns}")
        
        # Show sample data
        print("\n4. Sample Data:")
        df.show()
        
        # Test transformations
        print("\n5. Testing transformations...")
        filtered_df = df.filter(df.age > 25)
        print(f"   ✓ Filter operation: {filtered_df.count()} rows where age > 25")
        
        grouped_df = df.groupBy("department").count()
        print(f"   ✓ Group by operation: {grouped_df.count()} departments")
        
        print("\n" + "=" * 60)
        print("✓ SparkSession verification completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during SparkSession verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Optional: Stop session after verification
        # SparkSessionManager.stop_session()
        pass


if __name__ == "__main__":
    success = verify_spark_session()
    sys.exit(0 if success else 1)
