from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.customer import Customer
from ..schemas.customer import CustomerRegister, CustomerLogin, CustomerOut, Token
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: CustomerRegister, db: Session = Depends(get_db)):
    """Register a new customer account."""
    existing = db.query(Customer).filter(Customer.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email already registered", "code": "EMAIL_EXISTS"}
        )

    import random
    cust_num = f"CUST{random.randint(100, 999):03d}"
    phone_val = payload.phone or f"+9198{random.randint(10000000, 99999999)}"

    new_customer = Customer(
        customer_id=cust_num,
        name=payload.name,
        email=payload.email,
        phone=phone_val,
        password_hash=hash_password(payload.password)
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    access_token = create_access_token(data={"sub": new_customer.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=CustomerOut.model_validate(new_customer)
    )

@router.post("/login", response_model=Token)
def login(payload: CustomerLogin, db: Session = Depends(get_db)):
    """Authenticate customer with email and password."""
    customer = db.query(Customer).filter(Customer.email == payload.email).first()
    if not customer or not verify_password(payload.password, customer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid email or password", "code": "INVALID_CREDENTIALS"}
        )

    access_token = create_access_token(data={"sub": customer.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=CustomerOut.model_validate(customer)
    )

@router.get("/me", response_model=CustomerOut)
def get_current_customer(current_user: Customer = Depends(get_current_user)):
    """Retrieve authenticated customer profile."""
    return current_user
