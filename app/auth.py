from fastapi import HTTPException, status
from app.config import config
import hashlib
import time

class AuthService:
    def __init__(self):
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_time = 300  # 5 minutes
    
    def verify_secret(self, email: str, secret: str) -> bool:
        # Rate limiting check
        if self._is_rate_limited(email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Try again later."
            )
        
        # Verify credentials
        if email == config.EMAIL and secret == config.SECRET:
            self._clear_failed_attempts(email)
            return True
        else:
            self._record_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid email or secret"
            )
    
    def _is_rate_limited(self, email: str) -> bool:
        if email in self.failed_attempts:
            attempts, first_attempt = self.failed_attempts[email]
            if attempts >= self.max_attempts:
                if time.time() - first_attempt < self.lockout_time:
                    return True
                else:
                    # Reset after lockout period
                    del self.failed_attempts[email]
        return False
    
    def _record_failed_attempt(self, email: str):
        if email in self.failed_attempts:
            attempts, first_attempt = self.failed_attempts[email]
            self.failed_attempts[email] = (attempts + 1, first_attempt)
        else:
            self.failed_attempts[email] = (1, time.time())
    
    def _clear_failed_attempts(self, email: str):
        if email in self.failed_attempts:
            del self.failed_attempts[email]

auth_service = AuthService()