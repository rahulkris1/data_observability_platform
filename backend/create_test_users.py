"""Create test users for development"""
import sys
sys.path.append('.')

from app.core.database import SessionLocal
from app.services.auth_service import AuthService

def create_test_users():
    """Create test users for development"""
    db = SessionLocal()
    auth_service = AuthService(db)
    
    try:
        # Create admin user
        print("Creating test users...")
        
        # Check if admin exists
        admin = auth_service.get_user_by_email("admin@test.com")
        if not admin:
            admin = auth_service.create_user(
                email="admin@test.com",
                password="admin123",
                full_name="Admin User",
                role="admin"
            )
            print(f"✅ Created admin user: {admin.email}")
        else:
            print(f"ℹ️  Admin user already exists: {admin.email}")
        
        # Create regular viewer user
        viewer = auth_service.get_user_by_email("user@test.com")
        if not viewer:
            viewer = auth_service.create_user(
                email="user@test.com",
                password="user123",
                full_name="Test User",
                role="viewer"
            )
            print(f"✅ Created viewer user: {viewer.email}")
        else:
            print(f"ℹ️  Viewer user already exists: {viewer.email}")
        
        print("\n" + "="*60)
        print("Test Users Created Successfully!")
        print("="*60)
        print("\nLogin Credentials:")
        print("\n1. Admin User:")
        print("   Email: admin@test.com")
        print("   Password: admin123")
        print("\n2. Regular User:")
        print("   Email: user@test.com")
        print("   Password: user123")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
