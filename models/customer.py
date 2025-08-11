import enum
from sqlalchemy import Column, Integer, String, Enum, JSON
from db.database import Base

class CustomerType(str, enum.Enum):
    student = "student"
    professional = "professional"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    customer_type = Column(Enum(CustomerType), nullable=False)
    responses = Column(JSON)