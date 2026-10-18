from pydantic import BaseModel
from typing import Optional
import datetime

class CustomerRegister(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str

class CustomerLogin(BaseModel):
    email: str
    password: str

class CustomerOut(BaseModel):
    id: int
    customer_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CustomerOut
