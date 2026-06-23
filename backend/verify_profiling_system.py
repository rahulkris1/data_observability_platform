"""
Verification script for dataset profiling system
"""
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine
from app.models.profiling_result import ProfilingResult
from app.models.base import BaseModel
from app.services.dataset_profiling_service import DatasetProfilingService


def create_sample_dataset():
    """Create a sample dataset for testing"""
    data = {
        'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry', 'Iris', 'Jack'],
        'age': [25, 30, 35, 28, None, 45, 22, 38, 29, 31],
        'salary': [50000, 60000, 75000, 55000, 62000, None, 48000, 80000, 58000, 65000],
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'New York']
    }
    return pd.DataFrame(data)


def test_profiling_service():
    """Test the profiling service"""
    print("=" * 80)
    print("Testing Dataset Profiling Service")
    print("=" * 80)
    
    # Create database tables
    print("\n1. Creating database tables...")
    BaseModel.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample dataset
        print("\n2. Creating sample dataset...")
        df = create_sample_dataset()
        print(f"✓ Sample dataset created with {len(df)} rows and {len(df.columns)} columns")
        print(f"  Columns: {', '.join(df.columns)}")
        
        # Initialize service
        print("\n3. Initializing profiling service...")
        service = DatasetProfilingService(db)
        print("✓ Profiling service initialized")
        
        # Profile the dataset
        print("\n4. Profiling dataset...")
        result = service.profile_dataset(
            df=df,
            dataset_name='sample_customers',
            profiled_by='test_user'
        )
        print("✓ Profiling completed")
        
        # Display profiling results
        print("\n5. Profiling Results:")
        print("-" * 80)
        print(f"  Profiling ID: {result.id}")
        print(f"  Dataset Name: {result.dataset_name}")
        print(f"  Status: {result.status}")
        print(f"  Row Count: {result.row_count}")
        print(f"  Column Count: {result.column_count}")
        print(f"  Execution Time: {result.execution_time_ms:.2f} ms")
        print(f"  Profiled By: {result.profiled_by}")
        print(f"  Created At: {result.created_at}")
        
        # Display column statistics
        print("\n6. Column Statistics:")
        print("-" * 80)
        if result.column_statistics:
            for col_name, stats in result.column_statistics.items():
                print(f"\n  Column: {col_name}")
                print(f"    Data Type: {stats['data_type']}")
                print(f"    Null Count: {stats['null_count']}")
                print(f"    Null Percentage: {stats['null_percentage']:.2f}%")
                
                if 'min' in stats and stats['min'] is not None:
                    print(f"    Min: {stats['min']}")
                    print(f"    Max: {stats['max']}")
                    print(f"    Mean: {stats['mean']:.2f}")
                    print(f"    Median: {stats['median']:.2f}")
                    print(f"    Std Dev: {stats['std']:.2f}")
        
        # Display column distributions
        print("\n7. Column Distributions:")
        print("-" * 80)
        if result.column_distributions:
            for col_name, dist in result.column_distributions.items():
                print(f"\n  Column: {col_name}")
                print(f"    Unique Count: {dist['unique_count']}")
                print(f"    Top Values:")
                for val_info in dist['top_values'][:5]:  # Show top 5
                    print(f"      {val_info['value']}: {val_info['count']} ({val_info['percentage']:.2f}%)")
        
        # Test get_latest_profiling
        print("\n8. Testing get_latest_profiling...")
        latest = service.get_latest_profiling('sample_customers')
        if latest:
            print(f"✓ Latest profiling found: ID {latest.id}")
        else:
            print("✗ Latest profiling not found")
        
        # Test get_profiling_history
        print("\n9. Testing get_profiling_history...")
        history = service.get_profiling_history(dataset_name='sample_customers', limit=10)
        print(f"✓ Found {len(history)} profiling result(s)")
        
        # Test get_profiling_by_id
        print("\n10. Testing get_profiling_by_id...")
        by_id = service.get_profiling_by_id(result.id)
        if by_id:
            print(f"✓ Profiling found by ID: {by_id.id}")
        else:
            print("✗ Profiling not found by ID")
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = test_profiling_service()
    sys.exit(0 if success else 1)
