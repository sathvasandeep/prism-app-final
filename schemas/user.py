from pydantic import BaseModel, EmailStr
from typing import Literal

class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    customer_type: Literal["student", "working"]

class CustomerOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    customer_type: str

    class Config:
        orm_mode = True