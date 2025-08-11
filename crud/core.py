# crud/core.py
from sqlalchemy.orm import Session
from models.core import Profession, Department, Role

def get_all_professions(db: Session):
    return db.query(Profession).all()

def get_all_departments(db: Session):
    return db.query(Department).all()

def get_all_roles(db: Session):
    return db.query(Role).all()