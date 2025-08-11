from sqlalchemy.orm import Session
from models.customer import Customer
from schemas.customer import CustomerCreate

def create_customer(db: Session, customer_data: CustomerCreate):
    customer_dict = customer_data.dict()
    db_customer = Customer(**customer_dict)  # don't rename anything
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer
def get_customer_by_email(db: Session, email: str):
    return db.query(Customer).filter(Customer.email == email).first()