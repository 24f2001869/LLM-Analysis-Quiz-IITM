import pytest
from app.auth import AuthService

def test_valid_credentials():
    """Test authentication with valid credentials"""
    auth_service = AuthService()
    assert auth_service.verify_secret("24f2001869@ds.study.iitm.ac.in", "#Rahul@2005#") == True

def test_invalid_credentials():
    """Test authentication with invalid credentials"""
    auth_service = AuthService()
    
    with pytest.raises(Exception):
        auth_service.verify_secret("24f2001869@ds.study.iitm.ac.in", "wrong_secret")

def test_rate_limiting_logic():
    """Test rate limiting logic"""
    auth_service = AuthService()
    email = "test@example.com"
    
    # Record multiple failed attempts
    for i in range(5):
        auth_service._record_failed_attempt(email)
    
    # Should be rate limited after 5 attempts
    assert auth_service._is_rate_limited(email) == True

def test_clear_failed_attempts():
    """Test clearing failed attempts"""
    auth_service = AuthService()
    email = "test@example.com"
    
    # Record failed attempt
    auth_service._record_failed_attempt(email)
    auth_service._clear_failed_attempts(email)
    
    # Should not be rate limited after clearing
    assert auth_service._is_rate_limited(email) == False