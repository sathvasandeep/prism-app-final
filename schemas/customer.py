from pydantic import BaseModel
from typing import Dict
from models.customer import CustomerType

class CustomerBase(BaseModel):
    name: str
    email: str
    customer_type: CustomerType
    responses: Dict[str, str]

class CustomerCreate(CustomerBase):
    pass

class CustomerOut(CustomerBase):
    id: int

    class Config:
        from_attributes = True