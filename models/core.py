# models/core.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Profession(Base):
    __tablename__ = "professions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    #profession_id = Column(Integer, ForeignKey("professions.id"))

# models/core.py
class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.md"))
    title = Column(String(255))
    description_md = Column(Text)
    day_to_day_md = Column(Text)  