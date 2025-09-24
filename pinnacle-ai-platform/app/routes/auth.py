"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.core.config import settings

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    # TODO: Implement actual user authentication
    # For now, accept any username/password combination
    
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    # Create JWT token
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    to_encode = {
        "sub": request.username,
        "exp": expire,
        "iat": datetime.utcnow().timestamp()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret, 
        algorithm=settings.jwt_algorithm
    )
    
    return TokenResponse(
        access_token=encoded_jwt,
        expires_in=settings.jwt_expiration_hours * 3600
    )

@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user():
    """Get current user information"""
    # TODO: Implement with JWT token validation
    return {
        "username": "admin",
        "role": "administrator",
        "permissions": ["read", "write", "admin"]
    }
