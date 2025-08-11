from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from db.database import get_db
from models import Profession, Department, Role, DepartmentProfessionMap, RoleDepartmentMap

router = APIRouter()

@router.get("/api/config/stage1")
def get_stage1_config(db: Session = Depends(get_db)):
    # Fetch all professions
    professions = db.query(Profession).all()
    
    # Fetch mappings
    dept_prof_map = db.query(DepartmentProfessionMap).all()
    role_dept_map = db.query(RoleDepartmentMap).all()
    
    # Fetch all departments and roles
    departments = db.query(Department).all()
    roles = db.query(Role).all()

    # Build profession -> { department -> [roles] } map
    data = {}

    for prof in professions:
        # Departments mapped to this profession
        mapped_depts = [dp.department_id for dp in dept_prof_map if dp.profession_id == prof.id]
        dept_map = {}

        for dept in departments:
            if dept.id in mapped_depts:
                # Roles mapped to this department
                mapped_roles = [rd.role_id for rd in role_dept_map if rd.department_id == dept.id]
                role_names = [r.name for r in roles if r.id in mapped_roles]
                dept_map[dept.name] = role_names
        
        data[prof.name] = dept_map

    return {
        "professionalRolesData": data,
        "archetypes": [
            {
                "name": "Analytical Strategist",
                "description": "Data-driven decision maker...",
                "examples": ["Management Consultant"]
            },
            {
                "name": "Empathetic People Leader",
                "description": "Human-centered leader...",
                "examples": ["Team Manager"]
            }
        ]
    }