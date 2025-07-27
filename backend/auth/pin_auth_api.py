"""
PIN Authentication API endpoints for Dum Social Agent
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from .pin_auth import PinAuthService
from utils.logger import logger
import time
from collections import defaultdict

# Rate limiting for authentication attempts
auth_attempts = defaultdict(list)
MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes

router = APIRouter(prefix="/auth", tags=["PIN Authentication"])

# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    pin: str

class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[dict] = None
    error: Optional[str] = None

class ResetRequest(BaseModel):
    email: EmailStr

class ResetResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class ResetPinRequest(BaseModel):
    token: str
    new_pin: str

class AddUserRequest(BaseModel):
    email: EmailStr
    name: str
    pin: str

def check_rate_limit(client_ip: str, email: str) -> bool:
    """Check if the client has exceeded rate limits"""
    current_time = time.time()
    key = f"{client_ip}:{email}"
    
    # Clean old attempts
    auth_attempts[key] = [
        attempt_time for attempt_time in auth_attempts[key]
        if current_time - attempt_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if rate limit exceeded
    if len(auth_attempts[key]) >= MAX_ATTEMPTS:
        return False
    
    # Add current attempt
    auth_attempts[key].append(current_time)
    return True

def get_pin_auth_service() -> PinAuthService:
    """Dependency to get PIN auth service"""
    return PinAuthService()

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: PinAuthService = Depends(get_pin_auth_service)
):
    """
    Authenticate user with email and PIN
    """
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Check rate limiting
        if not check_rate_limit(client_ip, request.email):
            logger.warning(f"Rate limit exceeded for {request.email} from {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please try again later."
            )
        
        # Validate PIN format (should be 4-6 digits)
        if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
            return LoginResponse(
                success=False,
                error="Invalid PIN format"
            )
        
        # Authenticate user
        result = auth_service.authenticate_user(request.email, request.pin)
        
        if result['success']:
            logger.info(f"Successful authentication for {request.email} from {client_ip}")
            return LoginResponse(
                success=True,
                message="Authentication successful",
                user=result.get('user')
            )
        else:
            logger.warning(f"Failed authentication for {request.email} from {client_ip}: {result.get('error')}")
            return LoginResponse(
                success=False,
                error=result.get('error', 'Authentication failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/request-reset", response_model=ResetResponse)
async def request_pin_reset(
    request: ResetRequest,
    http_request: Request,
    auth_service: PinAuthService = Depends(get_pin_auth_service)
):
    """
    Request PIN reset via email
    """
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Check rate limiting for reset requests
        if not check_rate_limit(client_ip, f"reset:{request.email}"):
            logger.warning(f"Rate limit exceeded for reset request {request.email} from {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many reset requests. Please try again later."
            )
        
        result = auth_service.generate_reset_token(request.email)
        
        if result['success']:
            logger.info(f"Reset token generated for {request.email} from {client_ip}")
            return ResetResponse(
                success=True,
                message="Reset email sent successfully"
            )
        else:
            logger.warning(f"Failed to generate reset token for {request.email}: {result.get('error')}")
            # Don't reveal if user exists or not for security
            return ResetResponse(
                success=True,
                message="If the email exists in our system, a reset link has been sent"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reset-pin", response_model=ResetResponse)
async def reset_pin(
    request: ResetPinRequest,
    http_request: Request,
    auth_service: PinAuthService = Depends(get_pin_auth_service)
):
    """
    Reset PIN using reset token
    """
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Validate new PIN format
        if not request.new_pin.isdigit() or len(request.new_pin) < 4 or len(request.new_pin) > 6:
            return ResetResponse(
                success=False,
                error="PIN must be 4-6 digits"
            )
        
        result = auth_service.reset_pin_with_token(request.token, request.new_pin)
        
        if result['success']:
            logger.info(f"PIN reset successful from {client_ip}")
            return ResetResponse(
                success=True,
                message="PIN reset successfully"
            )
        else:
            logger.warning(f"Failed PIN reset from {client_ip}: {result.get('error')}")
            return ResetResponse(
                success=False,
                error=result.get('error', 'Failed to reset PIN')
            )
            
    except Exception as e:
        logger.error(f"PIN reset error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/add-user", response_model=ResetResponse)
async def add_authorized_user(
    request: AddUserRequest,
    http_request: Request,
    auth_service: PinAuthService = Depends(get_pin_auth_service)
):
    """
    Add new authorized user (admin endpoint)
    This endpoint should be protected with additional authentication in production
    """
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Validate PIN format
        if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
            return ResetResponse(
                success=False,
                error="PIN must be 4-6 digits"
            )
        
        result = auth_service.add_authorized_user(request.email, request.name, request.pin)
        
        if result['success']:
            logger.info(f"New user added: {request.email} from {client_ip}")
            return ResetResponse(
                success=True,
                message="User added successfully"
            )
        else:
            logger.warning(f"Failed to add user {request.email}: {result.get('error')}")
            return ResetResponse(
                success=False,
                error=result.get('error', 'Failed to add user')
            )
            
    except Exception as e:
        logger.error(f"Add user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {"status": "ok", "service": "pin_auth"}
