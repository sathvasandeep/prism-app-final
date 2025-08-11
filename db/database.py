from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# Replace this with your actual DB URL
DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/prism_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ THIS FUNCTION is what you're missing
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()