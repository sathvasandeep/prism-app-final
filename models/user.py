from sqlalchemy import Column, Integer, String, Enum
from db.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    customer_type = Column(Enum("student", "working", name="customer_type_enum"))