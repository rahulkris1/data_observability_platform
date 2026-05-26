"""Test Alembic migrations setup"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_alembic_config():
    """Test that Alembic configuration is properly set up"""
    print("=" * 60)
    print("Testing Alembic Configuration")
    print("=" * 60)
    
    # Check if alembic.ini exists
    alembic_ini = backend_dir / "alembic.ini"
    if alembic_ini.exists():
        print("✓ alembic.ini found")
    else:
        print("✗ alembic.ini not found")
        return False
    
    # Check if alembic/env.py exists
    env_py = backend_dir / "alembic" / "env.py"
    if env_py.exists():
        print("✓ alembic/env.py found")
    else:
        print("✗ alembic/env.py not found")
        return False
    
    # Check if alembic/versions directory exists
    versions_dir = backend_dir / "alembic" / "versions"
    if versions_dir.exists():
        print("✓ alembic/versions directory found")
    else:
        print("✗ alembic/versions directory not found")
        return False
    
    # Try importing alembic
    try:
        import alembic
        print(f"✓ Alembic package available")
    except ImportError:
        print("✗ Alembic package not installed")
        print("  Run: pip install -r requirements.txt")
        return False
    
    # Test imports from env.py
    try:
        from app.core.database import Base
        from app.core.config import settings
        print("✓ Can import Base and settings")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    print("\n" + "-" * 60)
    print("Alembic Commands:")
    print("  Initialize first migration:")
    print("    alembic revision --autogenerate -m 'Initial migration'")
    print("  Apply migrations:")
    print("    alembic upgrade head")
    print("  Check current version:")
    print("    alembic current")
    print("  View history:")
    print("    alembic history")
    
    return True


if __name__ == "__main__":
    success = test_alembic_config()
    print("\n" + "=" * 60)
    if success:
        print("Alembic configuration test passed! ✓")
    else:
        print("Alembic configuration test failed! ✗")
    print("=" * 60)
    sys.exit(0 if success else 1)
