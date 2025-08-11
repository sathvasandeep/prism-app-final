from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.user import CustomerCreate, CustomerOut
from crud.user import create_customer

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/customers/", response_model=CustomerOut)
def register_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, customer)