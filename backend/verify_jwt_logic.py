"""Simple verification script for JWT token logic (no database required)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


def verify_jwt_logic():
    """Verify JWT token generation and validation logic"""
    print("🔐 Verifying JWT Token Logic (No Database Required)\n")
    
    # Test 1: Password hashing
    print("1. Testing password hashing...")
    try:
        test_password = "test123"
        # Ensure password is bytes and within bcrypt limits
        hashed = get_password_hash(test_password)
        is_valid = verify_password(test_password, hashed)
        
        if is_valid:
            print("   ✓ Password hashing works correctly")
            print(f"   Password: {test_password}")
            print(f"   Hashed (first 50 chars): {hashed[:50]}...")
        else:
            print("   ✗ Password verification failed")
            return False
    except Exception as e:
        print(f"   ✗ Password hashing error: {e}")
        return False
    
    print()
    
    # Test 2: JWT token generation
    print("2. Testing JWT token generation...")
    try:
        token_data = {
            "sub": "test@example.com",
            "role": "admin",
            "user_id": 1
        }
        
        token, expires_at = create_access_token(data=token_data)
        
        print("   ✓ Token generated successfully")
        print(f"   Token (first 50 chars): {token[:50]}...")
        print(f"   Expires at: {expires_at}")
    except Exception as e:
        print(f"   ✗ Token generation error: {e}")
        return False
    
    print()
    
    # Test 3: JWT token decoding
    print("3. Testing JWT token decoding...")
    try:
        payload = decode_access_token(token)
        
        if payload and payload.get("sub") == "test@example.com":
            print("   ✓ Token decoded successfully")
            print(f"   Email: {payload.get('sub')}")
            print(f"   Role: {payload.get('role')}")
            print(f"   User ID: {payload.get('user_id')}")
        else:
            print("   ✗ Token decoding failed or payload invalid")
            return False
    except Exception as e:
        print(f"   ✗ Token decoding error: {e}")
        return False
    
    print()
    
    # Test 4: Invalid token handling
    print("4. Testing invalid token handling...")
    try:
        invalid_payload = decode_access_token("invalid.token.here")
        
        if invalid_payload is None:
            print("   ✓ Invalid token correctly rejected")
        else:
            print("   ✗ Invalid token was accepted")
            return False
    except Exception as e:
        print(f"   ✗ Error handling invalid token: {e}")
        return False
    
    print()
    
    # Test 5: Password mismatch
    print("5. Testing password mismatch detection...")
    try:
        wrong_password = "wrongpassword"
        is_match = verify_password(wrong_password, hashed)
        
        if not is_match:
            print("   ✓ Password mismatch correctly detected")
        else:
            print("   ✗ Wrong password was accepted")
            return False
    except Exception as e:
        print(f"   ✗ Password verification error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ All JWT logic tests passed!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Start the PostgreSQL database")
    print("2. Run: alembic upgrade head")
    print("3. Run: python verify_auth_system.py (for full database tests)")
    print("4. Start backend: uvicorn app.main:app --reload")
    print("5. Start frontend: cd ../frontend && npm run dev")
    print("\nTest the login at: http://localhost:3000/login")
    
    return True


if __name__ == "__main__":
    success = verify_jwt_logic()
    sys.exit(0 if success else 1)
