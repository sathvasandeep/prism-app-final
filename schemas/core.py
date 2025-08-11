# schemas/core.py
from pydantic import BaseModel
from typing import Optional

class ProfessionSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class DepartmentSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class RoleSchema(BaseModel):
    id: int
    name: str
    department_id: int
    title: Optional[str] = None
    description_md: Optional[str] = None
    day_to_day_md: Optional[str] = None

    class Config:
        orm_mode = True