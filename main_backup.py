# main.py - FastAPI back-end for the PRISM Framework
# ==================================================

import os
import logging
import json
import asyncio
from typing import Dict, List, Optional
import aiomysql
import google.generativeai as genai
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- ENVIRONMENT LOADING ---
API_KEY = os.getenv("GEMINI_API_KEY")
DISABLE_AI = os.getenv("DISABLE_AI", "1") == "1"

# Configure Gemini if API key is available
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        logging.info("Gemini client configured")
    except Exception as e:
        logging.error(f"Gemini configure failed: {e}")
        API_KEY = None
else:
    logging.warning("API_KEY missing – AI routes disabled.")

# --- DATABASE HELPER ---
DB_POOL = None

# FastAPI app
app = FastAPI(title="PRISM Framework API")

# CORS settings
origins = [
    "http://localhost",
    "http://localhost:8080", 
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def on_startup():
    global DB_POOL
    try:
        DB_POOL = await aiomysql.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=3306,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            autocommit=True,
        )
        logging.info("MySQL connection pool created.")
        await init_db()
    except Exception as e:
        logging.exception("Failed to create MySQL pool: %s", e)
        raise

@app.on_event("shutdown")
async def shutdown():
    if DB_POOL:
        DB_POOL.close()
        await DB_POOL.wait_closed()
        logging.info("Database connection pool closed.")

async def get_db_connection():
    if DB_POOL is None:
        raise HTTPException(status_code=500, detail="Database connection pool not available.")
    async with DB_POOL.acquire() as conn:
        yield conn

# Database initialization
async def init_db():
    """Initialize database tables"""
    conn = await get_db_connection().__anext__()
    try:
        # Create basic tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS professions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profession_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (profession_id) REFERENCES professions(id)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                department_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS role_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profile_name VARCHAR(255) NOT NULL UNIQUE,
                profession_id INT NOT NULL,
                department_id INT NOT NULL,
                role_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profession_id) REFERENCES professions(id),
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS skive_ratings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profile_id INT NOT NULL,
                category VARCHAR(50) NOT NULL,
                subcategory VARCHAR(100) NOT NULL,
                score DECIMAL(3,1) NOT NULL,
                description TEXT,
                FOREIGN KEY (profile_id) REFERENCES role_profiles(id),
                UNIQUE KEY unique_rating (profile_id, category, subcategory)
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS role_profile_objectives (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profile_id INT NOT NULL,
                skive_subcategory VARCHAR(100) NOT NULL,
                objective_text TEXT NOT NULL,
                difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES role_profiles(id),
                UNIQUE KEY unique_objective (profile_id, skive_subcategory)
            )
        """)
        
        # Create competency descriptors table for dynamic archetypes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS competency_descriptors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                skive_category ENUM('skills', 'knowledge', 'identity', 'values', 'ethics') NOT NULL,
                subcategory VARCHAR(100) NOT NULL,
                proficiency_tier ENUM('low', 'medium', 'high') NOT NULL,
                descriptor_phrase TEXT NOT NULL,
                narrative_type ENUM('signature', 'supporting', 'foundational') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_descriptor (skive_category, subcategory, proficiency_tier, narrative_type)
            )
        """)
        
        # Seed data
        await _seed_professions_departments_roles(conn)
        await _seed_competency_descriptors(conn)
        
        await conn.commit()
        logging.info("Database initialized successfully")
    except Exception as e:
        await conn.rollback()
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        await conn.ensure_closed()

# Seed functions would go here...
async def _seed_professions_departments_roles(conn):
    # Implementation for seeding basic data
    pass

async def _seed_competency_descriptors(conn):
    # Implementation for seeding phrase library
    pass

# Basic health check
@app.get("/")
async def root():
    return {"message": "PRISM Framework API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
