"""
Simplified authentication API for testing Dum Social Agent authentication
This is a standalone server for testing the PIN authentication system
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
import secrets
import time
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dum Social Auth API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# In-memory storage for demo (replace with Supabase in production)
authorized_users = {}
reset_tokens = {}

# Rate limiting
auth_attempts = defaultdict(list)
MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes

# Pydantic models
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

def hash_pin(pin: str) -> str:
    """Hash a PIN using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pin.encode('utf-8'), salt).decode('utf-8')

def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against its hash"""
    return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))

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

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """Authenticate user with email and PIN"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Check rate limiting
        if not check_rate_limit(client_ip, request.email):
            logger.warning(f"Rate limit exceeded for {request.email} from {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please try again later."
            )
        
        # Validate PIN format
        if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
            return LoginResponse(
                success=False,
                error="Invalid PIN format"
            )
        
        # Check if user exists
        if request.email not in authorized_users:
            logger.warning(f"User not found: {request.email}")
            return LoginResponse(
                success=False,
                error="User not found or not authorized"
            )
        
        user_data = authorized_users[request.email]
        
        # Verify PIN
        if not verify_pin(request.pin, user_data['pin_hash']):
            logger.warning(f"Invalid PIN for {request.email}")
            return LoginResponse(
                success=False,
                error="Invalid PIN"
            )
        
        logger.info(f"Successful authentication for {request.email} from {client_ip}")
        return LoginResponse(
            success=True,
            message="Authentication successful",
            user={
                "id": user_data['id'],
                "email": request.email,
                "name": user_data['name']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/request-reset", response_model=ResetResponse)
async def request_pin_reset(request: ResetRequest, http_request: Request):
    """Request PIN reset via email (demo - just generates token)"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Check rate limiting
        if not check_rate_limit(client_ip, f"reset:{request.email}"):
            logger.warning(f"Rate limit exceeded for reset request {request.email} from {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many reset requests. Please try again later."
            )
        
        # Generate reset token (in production, send via email)
        reset_token = secrets.token_urlsafe(32)
        reset_tokens[reset_token] = {
            'email': request.email,
            'expires': time.time() + 3600  # 1 hour
        }
        
        logger.info(f"Reset token generated for {request.email}: {reset_token}")
        return ResetResponse(
            success=True,
            message=f"Reset token generated (demo): {reset_token}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset request error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/reset-pin", response_model=ResetResponse)
async def reset_pin(request: ResetPinRequest, http_request: Request):
    """Reset PIN using reset token"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Validate new PIN format
        if not request.new_pin.isdigit() or len(request.new_pin) < 4 or len(request.new_pin) > 6:
            return ResetResponse(
                success=False,
                error="PIN must be 4-6 digits"
            )
        
        # Check if token exists and is valid
        if request.token not in reset_tokens:
            return ResetResponse(
                success=False,
                error="Invalid reset token"
            )
        
        token_data = reset_tokens[request.token]
        
        # Check if token is expired
        if time.time() > token_data['expires']:
            del reset_tokens[request.token]
            return ResetResponse(
                success=False,
                error="Reset token has expired"
            )
        
        email = token_data['email']
        
        # Update user PIN
        if email in authorized_users:
            authorized_users[email]['pin_hash'] = hash_pin(request.new_pin)
            del reset_tokens[request.token]
            
            logger.info(f"PIN reset successful for {email} from {client_ip}")
            return ResetResponse(
                success=True,
                message="PIN reset successfully"
            )
        else:
            return ResetResponse(
                success=False,
                error="User not found"
            )
        
    except Exception as e:
        logger.error(f"PIN reset error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/add-user", response_model=ResetResponse)
async def add_authorized_user(request: AddUserRequest, http_request: Request):
    """Add new authorized user"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Validate PIN format
        if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
            return ResetResponse(
                success=False,
                error="PIN must be 4-6 digits"
            )
        
        # Check if user already exists
        if request.email in authorized_users:
            return ResetResponse(
                success=False,
                error="User already exists"
            )
        
        # Add user
        user_id = secrets.token_urlsafe(16)
        authorized_users[request.email] = {
            'id': user_id,
            'name': request.name,
            'pin_hash': hash_pin(request.pin),
            'created_at': time.time()
        }
        
        logger.info(f"New user added: {request.email} from {client_ip}")
        return ResetResponse(
            success=True,
            message="User added successfully"
        )
        
    except Exception as e:
        logger.error(f"Add user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {
        "status": "ok", 
        "service": "dum_social_auth", 
        "users_count": len(authorized_users),
        "active_tokens": len(reset_tokens)
    }

@app.get("/api/health")
async def health_check():
    """General health check"""
    return {"status": "ok", "service": "dum_social_auth_api"}

if __name__ == "__main__":
    import uvicorn
    
    # Add a demo user for testing
    demo_email = "demo@dumsocial.com"
    demo_pin = "1234"
    authorized_users[demo_email] = {
        'id': 'demo-user-id',
        'name': 'Demo User',
        'pin_hash': hash_pin(demo_pin),
        'created_at': time.time()
    }
    
    logger.info(f"Demo user created: {demo_email} with PIN: {demo_pin}")
    logger.info("Starting Dum Social Auth API server...")
    
    uvicorn.run(
        "simple_auth_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
