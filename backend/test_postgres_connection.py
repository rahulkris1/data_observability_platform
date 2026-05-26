"""Test PostgreSQL database connection"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.utils.db_utils import check_database_connection, create_all_tables
from app.core.config import settings


def main():
    """Test database connection and initialization"""
    print("=" * 60)
    print("Testing PostgreSQL Database Connection")
    print("=" * 60)
    
    # Display connection info
    print(f"\nDatabase Configuration:")
    print(f"  Host: {settings.POSTGRES_HOST}")
    print(f"  Port: {settings.POSTGRES_PORT}")
    print(f"  Database: {settings.POSTGRES_DB}")
    print(f"  User: {settings.POSTGRES_USER}")
    print(f"  URL: {settings.DATABASE_URL.replace(settings.POSTGRES_PASSWORD, '***')}")
    
    # Test connection
    print("\n" + "-" * 60)
    print("Testing database connection...")
    if check_database_connection():
        print("✓ Database connection successful!")
        
        # Try creating tables
        print("\n" + "-" * 60)
        print("Testing table creation...")
        try:
            create_all_tables()
            print("✓ Table creation successful!")
        except Exception as e:
            print(f"✗ Table creation failed: {e}")
            return False
            
        return True
    else:
        print("✗ Database connection failed!")
        print("\nTroubleshooting:")
        print("  1. Make sure PostgreSQL is running:")
        print("     docker-compose up -d postgres")
        print("  2. Check connection settings in .env or config.py")
        print("  3. Verify network connectivity to database")
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("All database tests passed! ✓")
    else:
        print("Database tests failed! ✗")
    print("=" * 60)
    sys.exit(0 if success else 1)
