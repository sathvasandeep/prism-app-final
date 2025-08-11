# models/mappings.py

from sqlalchemy import Column, Integer, ForeignKey
from db.database import Base

class DepartmentProfessionMap(Base):
    __tablename__ = 'department_profession_map'

    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    profession_id = Column(Integer, ForeignKey('professions.id'))

class RoleDepartmentMap(Base):
    __tablename__ = 'role_department_map'

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'))
    department_id = Column(Integer, ForeignKey('departments.id'))