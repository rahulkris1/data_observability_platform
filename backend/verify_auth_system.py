"""Verification script for JWT authentication flow"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.models.base import BaseModel
from app.services.auth_service import AuthService
from app.core.security import verify_password, get_password_hash


def verify_auth_system():
    """Verify JWT authentication system"""
    print("🔐 Verifying JWT Authentication System\n")
    
    # Create tables
    print("1. Creating database tables...")
    try:
        BaseModel.metadata.create_all(bind=engine)
        print("   ✓ Tables created successfully\n")
    except Exception as e:
        print(f"   ✗ Error creating tables: {e}\n")
        return False
    
    # Test database session
    print("2. Testing database connection...")
    try:
        db: Session = SessionLocal()
        print("   ✓ Database connected\n")
    except Exception as e:
        print(f"   ✗ Database connection failed: {e}\n")
        return False
    
    # Test password hashing
    print("3. Testing password hashing...")
    try:
        test_password = "test123"
        hashed = get_password_hash(test_password)
        is_valid = verify_password(test_password, hashed)
        
        if is_valid:
            print("   ✓ Password hashing works correctly\n")
        else:
            print("   ✗ Password verification failed\n")
            return False
    except Exception as e:
        print(f"   ✗ Password hashing error: {e}\n")
        return False
    
    # Test user creation
    print("4. Creating test users...")
    try:
        auth_service = AuthService(db)
        
        # Clean up existing test users
        db.query(User).filter(User.email.in_(["admin@test.com", "viewer@test.com"])).delete()
        db.commit()
        
        # Create admin user
        admin = auth_service.create_user(
            email="admin@test.com",
            password="admin123",
            full_name="Admin User",
            role="admin"
        )
        print(f"   ✓ Admin user created: {admin.email} (Role: {admin.role.value})")
        
        # Create viewer user
        viewer = auth_service.create_user(
            email="viewer@test.com",
            password="viewer123",
            full_name="Viewer User",
            role="viewer"
        )
        print(f"   ✓ Viewer user created: {viewer.email} (Role: {viewer.role.value})\n")
        
    except Exception as e:
        print(f"   ✗ User creation error: {e}\n")
        db.rollback()
        return False
    
    # Test authentication
    print("5. Testing user authentication...")
    try:
        # Test valid credentials
        user = auth_service.authenticate_user("admin@test.com", "admin123")
        if user:
            print(f"   ✓ Admin authentication successful: {user.email}")
        else:
            print("   ✗ Admin authentication failed")
            return False
        
        # Test invalid credentials
        user = auth_service.authenticate_user("admin@test.com", "wrongpassword")
        if user is None:
            print("   ✓ Invalid password correctly rejected")
        else:
            print("   ✗ Invalid password was accepted")
            return False
        
        # Test non-existent user
        user = auth_service.authenticate_user("fake@test.com", "password")
        if user is None:
            print("   ✓ Non-existent user correctly rejected\n")
        else:
            print("   ✗ Non-existent user was accepted\n")
            return False
            
    except Exception as e:
        print(f"   ✗ Authentication error: {e}\n")
        return False
    
    # Test JWT token generation
    print("6. Testing JWT token generation...")
    try:
        admin_user = db.query(User).filter(User.email == "admin@test.com").first()
        token, expires_at = auth_service.create_token_for_user(admin_user)
        
        print(f"   ✓ Token generated successfully")
        print(f"   Token (first 50 chars): {token[:50]}...")
        print(f"   Expires at: {expires_at}\n")
        
    except Exception as e:
        print(f"   ✗ Token generation error: {e}\n")
        return False
    
    # Test token verification
    print("7. Testing JWT token verification...")
    try:
        payload = auth_service.verify_token(token)
        
        if payload and payload.get("sub") == "admin@test.com":
            print(f"   ✓ Token verification successful")
            print(f"   User: {payload.get('sub')}")
            print(f"   Role: {payload.get('role')}")
            print(f"   User ID: {payload.get('user_id')}\n")
        else:
            print("   ✗ Token verification failed\n")
            return False
        
        # Test invalid token
        invalid_payload = auth_service.verify_token("invalid.token.here")
        if invalid_payload is None:
            print("   ✓ Invalid token correctly rejected\n")
        else:
            print("   ✗ Invalid token was accepted\n")
            return False
            
    except Exception as e:
        print(f"   ✗ Token verification error: {e}\n")
        return False
    
    # Cleanup
    db.close()
    
    print("=" * 60)
    print("✅ All JWT authentication tests passed!")
    print("=" * 60)
    print("\nTest Users Created:")
    print("  - Email: admin@test.com | Password: admin123 | Role: admin")
    print("  - Email: viewer@test.com | Password: viewer123 | Role: viewer")
    print("\nYou can now test the API endpoints:")
    print("  POST /api/v1/auth/login")
    print("  POST /api/v1/auth/verify")
    print("  GET  /api/v1/auth/me")
    
    return True


if __name__ == "__main__":
    success = verify_auth_system()
    sys.exit(0 if success else 1)
