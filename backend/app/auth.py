import datetime
import jwt
import hashlib
import hmac
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models.customer import Customer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    """Secure password hash using SHA-256 with HMAC secret salt."""
    salt = settings.SECRET_KEY.encode()
    pwd_hash = hmac.new(salt, password.encode(), hashlib.sha256).hexdigest()
    return f"sha256${pwd_hash}"

get_password_hash = hash_password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored hash."""
    expected_hash = hash_password(plain_password)
    return hmac.compare_digest(expected_hash, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Customer:
    """Authenticate bearer token and return active Customer object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer is None:
        raise credentials_exception
    return customer

def get_optional_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[Customer]:
    """Retrieve current user if token provided, otherwise return None (for guest/chat scenarios)."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        return db.query(Customer).filter(Customer.email == email).first()
    except Exception:
        return None

def get_current_admin_user(current_user: Customer = Depends(get_current_user)) -> Customer:
    """Ensure current authenticated user has admin/supervisor role from database."""
    if not current_user or getattr(current_user, "role", "customer").lower() not in ["admin", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. User does not have authorization."
        )
    return current_user

