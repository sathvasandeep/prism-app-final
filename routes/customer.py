from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.customer import CustomerCreate, CustomerOut
from crud.customer import create_customer, get_customer_by_email

router = APIRouter()

@router.post("/customers/", response_model=CustomerOut)
async def create_new_customer(
    customer: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # Debug log
    raw = await request.body()
    print("🔍 Raw request body:", raw.decode('utf-8'))

    # Actual logic
    existing = get_customer_by_email(db, customer.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_customer(db, customer)