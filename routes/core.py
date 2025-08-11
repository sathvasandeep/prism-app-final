# routes/core.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from crud.core import get_all_professions, get_all_departments, get_all_roles
from schemas.core import ProfessionSchema, DepartmentSchema, RoleSchema
from typing import List

router = APIRouter()

@router.get("/professions/", response_model=List[ProfessionSchema])
def fetch_professions(db: Session = Depends(get_db)):
    return get_all_professions(db)

@router.get("/departments/", response_model=List[DepartmentSchema])
def fetch_departments(db: Session = Depends(get_db)):
    return get_all_departments(db)

@router.get("/roles/", response_model=List[RoleSchema])
def fetch_roles(db: Session = Depends(get_db)):
    return get_all_roles(db)