# main.py - FastAPI back-end for the PRISM Framework
# ==================================================

import os
import json
import re
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

async def create_db_pool():
    """Create a new aiomysql pool using env vars."""
    global DB_POOL
    DB_POOL = await aiomysql.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        autocommit=True,
        minsize=1,
        maxsize=5,
    )
    logging.info("MySQL connection pool created.")

# FastAPI app
app = FastAPI(title="PRISM Framework API")

# CORS settings
origins = [
    "http://localhost",
    "http://localhost:8080", 
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5179",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5179"
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
    try:
        await create_db_pool()
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
    """Yield a live connection, recreating the pool if needed."""
    global DB_POOL
    if DB_POOL is None or getattr(DB_POOL, "_closed", False):
        await create_db_pool()
    try:
        async with DB_POOL.acquire() as conn:
            # Lightweight ping to ensure the connection is alive
            try:
                cur = await conn.cursor()
                await cur.execute("SELECT 1")
                await cur.fetchone()
                await cur.close()
            except Exception:
                # Connection might be stale; recreate pool and reacquire
                try:
                    DB_POOL.close()
                    await DB_POOL.wait_closed()
                except Exception:
                    pass
                await create_db_pool()
                async with DB_POOL.acquire() as conn2:
                    yield conn2
                    return
            yield conn
    except AttributeError:
        # Handle pool's internal broken connections (e.g., _reader None). Recreate pool.
        try:
            if DB_POOL is not None:
                DB_POOL.close()
                await DB_POOL.wait_closed()
        except Exception:
            pass
        await create_db_pool()
        async with DB_POOL.acquire() as conn:
            yield conn

# Database initialization
async def init_db():
    """Initialize database tables"""
    conn = await get_db_connection().__anext__()
    cursor = await conn.cursor()
    try:
        # Create basic tables
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS professions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            )
        """)
        
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profession_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (profession_id) REFERENCES professions(id)
            )
        """)
        
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                department_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        
        await cursor.execute("""
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
        
        await cursor.execute("""
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
        
        await cursor.execute("""
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
        await cursor.execute("""
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
        await cursor.close()
        await conn.ensure_closed()

# Seed functions
async def _seed_professions_departments_roles(conn):
    """Seed catalogue data by resolving IDs dynamically to avoid ID mismatches."""
    profession_names = ["Technology", "Healthcare", "Finance", "Insurance"]
    dept_seeds = [
        ("Technology", "Software Engineering"),
        ("Technology", "Product Management"),
        ("Technology", "Data Science"),
        ("Healthcare", "Clinical Operations"),
        ("Healthcare", "Nursing"),
        ("Finance", "Corporate Finance"),
        ("Finance", "Risk & Compliance"),
        ("Insurance", "Claims & Adjudication"),
        ("Insurance", "Underwriting"),
    ]
    role_seeds = [
        ("Technology", "Software Engineering", "Software Engineer"),
        ("Technology", "Product Management", "Product Manager"),
        ("Technology", "Data Science", "Data Scientist"),
        ("Healthcare", "Clinical Operations", "Clinical Coordinator"),
        ("Healthcare", "Nursing", "Registered Nurse"),
        ("Finance", "Corporate Finance", "Financial Analyst"),
        ("Finance", "Risk & Compliance", "Risk Analyst"),
        ("Insurance", "Claims & Adjudication", "Claims Adjuster"),
        ("Insurance", "Underwriting", "Underwriter"),
    ]

    cursor = await conn.cursor()
    try:
        # 1) Ensure professions exist and build name->id map
        prof_id_map: dict[str, int] = {}
        for pname in profession_names:
            # Insert if missing
            await cursor.execute("SELECT id FROM professions WHERE name=%s", (pname,))
            row = await cursor.fetchone()
            if not row:
                await cursor.execute("INSERT INTO professions (name) VALUES (%s)", (pname,))
                prof_id = cursor.lastrowid
            else:
                prof_id = row[0]
            prof_id_map[pname] = prof_id

        # 2) Ensure departments exist and build (prof_name, dept_name)->id map
        dept_id_map: dict[tuple[str, str], int] = {}
        for pname, dname in dept_seeds:
            prof_id = prof_id_map[pname]
            await cursor.execute(
                "SELECT id FROM departments WHERE profession_id=%s AND name=%s",
                (prof_id, dname),
            )
            row = await cursor.fetchone()
            if not row:
                await cursor.execute(
                    "INSERT INTO departments (profession_id, name) VALUES (%s, %s)",
                    (prof_id, dname),
                )
                dept_id = cursor.lastrowid
            else:
                dept_id = row[0]
            dept_id_map[(pname, dname)] = dept_id

        # 3) Ensure roles exist under correct departments
        for pname, dname, rname in role_seeds:
            dept_id = dept_id_map[(pname, dname)]
            await cursor.execute(
                "SELECT id FROM roles WHERE department_id=%s AND name=%s",
                (dept_id, rname),
            )
            row = await cursor.fetchone()
            if not row:
                await cursor.execute(
                    "INSERT INTO roles (department_id, name) VALUES (%s, %s)",
                    (dept_id, rname),
                )
            # else already present
    finally:
        await cursor.close()

from models.phrase_library import (
    COMPETENCY_DESCRIPTORS_SEED_DATA,
    get_proficiency_tier,
    get_narrative_type
)

async def _seed_competency_descriptors(conn):
    """Seed phrase library for dynamic archetype generation"""
    cursor = await conn.cursor()
    try:
        for skive_cat, subcat, tier, phrase, narrative_type in COMPETENCY_DESCRIPTORS_SEED_DATA:
            await cursor.execute(
                """INSERT IGNORE INTO competency_descriptors 
                   (skive_category, subcategory, proficiency_tier, descriptor_phrase, narrative_type)
                   VALUES (%s, %s, %s, %s, %s)""",
                (skive_cat, subcat, tier, phrase, narrative_type)
            )
    finally:
        await cursor.close()

# Dynamic archetype generation functions
def identify_signature_competencies(ratings: List[Dict], top_n: int = 3) -> List[Dict]:
    """Identify the top N highest-rated competencies as signature skills"""
    sorted_ratings = sorted(ratings, key=lambda x: float(x.get('score', 0)), reverse=True)
    return sorted_ratings[:top_n]

def categorize_by_proficiency_tier(ratings: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize ratings by proficiency tier (low/medium/high)"""
    tiers = {'low': [], 'medium': [], 'high': []}
    for rating in ratings:
        score = float(rating.get('score', 0))
        tier = get_proficiency_tier(score)
        tiers[tier].append({**rating, 'tier': tier})
    return tiers

async def generate_dynamic_archetype(ratings: List[Dict], skive_category: str, conn) -> Dict:
    """Generate dynamic archetype for a specific SKIVE category"""

    
    if not ratings:
        return {'narrative': f'No {skive_category} data available', 'signature_competencies': [], 'supporting_competencies': [], 'foundational_competencies': []}
    
    # Identify signature competencies (top 2-3 highest rated)
    signature_comps = identify_signature_competencies(ratings, top_n=2)
    
    # Categorize by proficiency tier
    tiers = categorize_by_proficiency_tier(ratings)
    
    # Get descriptor phrases from database
    narrative_parts = []
    
    # Build signature narrative
    if signature_comps:
        signature_phrases = []
        for comp in signature_comps:
            cursor = await conn.cursor(aiomysql.DictCursor)
            await cursor.execute(
                """SELECT descriptor_phrase FROM competency_descriptors 
                   WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = %s AND narrative_type = 'signature'""",
                (skive_category, comp.get('subcategory', ''), get_proficiency_tier(float(comp.get('score', 0))))
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                signature_phrases.append(result['descriptor_phrase'])
        
        if signature_phrases:
            narrative_parts.append(f"This role is defined by mastery of {', '.join(signature_phrases)}.")
    
    # Build supporting narrative for high-tier competencies
    high_tier_phrases = []
    for comp in tiers['high']:
        if comp not in signature_comps:  # Avoid duplicating signature competencies
            cursor = await conn.cursor(aiomysql.DictCursor)
            await cursor.execute(
                """SELECT descriptor_phrase FROM competency_descriptors 
                   WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = 'high' AND narrative_type = 'supporting'""",
                (skive_category, comp.get('subcategory', ''))
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                high_tier_phrases.append(result['descriptor_phrase'])
    
    if high_tier_phrases:
        narrative_parts.append(f"Supported by {', '.join(high_tier_phrases)}.")
    
    # Build foundational narrative for medium-tier competencies
    medium_tier_phrases = []
    for comp in tiers['medium'][:3]:  # Limit to top 3 medium competencies
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(
            """SELECT descriptor_phrase FROM competency_descriptors 
               WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = 'medium' AND narrative_type = 'foundational'""",
            (skive_category, comp.get('subcategory', ''))
        )
        result = await cursor.fetchone()
        await cursor.close()
        
        if result:
            medium_tier_phrases.append(result['descriptor_phrase'])
    
    if medium_tier_phrases:
        narrative_parts.append(f"Built upon a foundation of {', '.join(medium_tier_phrases)}.")
    
    return {
        'narrative': ' '.join(narrative_parts) if narrative_parts else f'Professional competence in {skive_category} with balanced skill distribution.',
        'signature_competencies': [comp.get('subcategory', '') for comp in signature_comps],
        'supporting_competencies': [comp.get('subcategory', '') for comp in tiers['high'] if comp not in signature_comps],
        'foundational_competencies': [comp.get('subcategory', '') for comp in tiers['medium'][:3]]
    }

# API Endpoints
@app.get("/")
async def root():
    return {"message": "PRISM Framework API is running"}

@app.get("/api/debug/role_profiles")
async def debug_role_profiles(conn = Depends(get_db_connection)):
    try:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute("SELECT id, profile_name, profession_id, department_id, role_id, created_at FROM role_profiles ORDER BY id DESC LIMIT 10")
        rows = await cursor.fetchall()
        await cursor.close()
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/role_profiles_schema")
async def debug_role_profiles_schema(conn = Depends(get_db_connection)):
    try:
        db_name = os.getenv("DB_NAME")
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(
            """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'role_profiles' 
            ORDER BY ordinal_position
            """,
            (db_name,)
        )
        cols = await cursor.fetchall()
        await cursor.close()
        return {"columns": cols}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/skive_schema")
async def debug_skive_schema(conn = Depends(get_db_connection)):
    try:
        db_name = os.getenv("DB_NAME")
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(
            """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'skive_ratings' 
            ORDER BY ordinal_position
            """,
            (db_name,)
        )
        cols = await cursor.fetchall()
        await cursor.close()
        return {"columns": cols}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/skive_rows/{profile_id}")
async def debug_skive_rows(profile_id: int, conn = Depends(get_db_connection)):
    try:
        db_name = os.getenv("DB_NAME")
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(
            """
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'skive_ratings'
            """,
            (db_name,)
        )
        cols = {row['column_name'] for row in (await cur.fetchall())}
        await cur.close()
        category_col = 'category' if 'category' in cols else ('dimension' if 'dimension' in cols else 'category')
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(f"SELECT id, {category_col} AS category, subcategory, score, description FROM skive_ratings WHERE profile_id=%s ORDER BY id DESC LIMIT 50", (profile_id,))
        rows = await cursor.fetchall()
        await cursor.close()
        return {"rows": rows}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/professions")
async def get_professions(conn = Depends(get_db_connection)):
    """List available professions"""
    try:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute("SELECT id, name FROM professions ORDER BY id")
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    except Exception as e:
        logging.error(f"Error fetching professions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch professions")

@app.get("/api/departments")
async def get_departments(profession_id: Optional[str] = None, conn = Depends(get_db_connection)):
    """List departments by profession"""
    try:
        # Gracefully handle missing/invalid ids
        if not profession_id:
            return []
        try:
            prof_id_int = int(profession_id)
        except Exception:
            return []
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(
            "SELECT id, name, profession_id FROM departments WHERE profession_id = %s ORDER BY id",
            (prof_id_int,)
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    except Exception as e:
        logging.error(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

@app.get("/api/roles")
async def get_roles(department_id: Optional[str] = None, conn = Depends(get_db_connection)):
    """List roles by department"""
    try:
        if not department_id:
            return []
        try:
            dept_id_int = int(department_id)
        except Exception:
            return []
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(
            "SELECT id, name, department_id FROM roles WHERE department_id = %s ORDER BY id",
            (dept_id_int,)
        )
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    except Exception as e:
        logging.error(f"Error fetching roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch roles")

# --- SIMULATIONS (Dashboard) ---
@app.get("/api/simulations")
async def list_simulations(conn = Depends(get_db_connection)):
    """Return a simple list of saved profiles for the dashboard.
    Uses `role_profiles` joined to get readable names. `updated_at` and `archetype`
    may be NULL depending on schema; the frontend tolerates missing values.
    """
    cursor = await conn.cursor(aiomysql.DictCursor)
    try:
        await cursor.execute(
            """
            SELECT
                rp.id,
                r.name AS specific_role,
                p.name AS profession,
                d.name AS department,
                NULL AS updated_at,
                NULL AS archetype
            FROM role_profiles rp
            LEFT JOIN roles r ON rp.role_id = r.id
            LEFT JOIN departments d ON rp.department_id = d.id
            LEFT JOIN professions p ON rp.profession_id = p.id
            ORDER BY rp.id DESC
            """
        )
        rows = await cursor.fetchall()
        return rows
    finally:
        await cursor.close()

@app.get("/api/simulations/{profile_id}")
async def get_simulation(profile_id: int, conn = Depends(get_db_connection)):
    """Return a saved profile payload by id. This is intentionally lightweight and
    returns the main identity columns plus names for display. The UI merges this
    with its initial template.
    """
    cursor = await conn.cursor(aiomysql.DictCursor)
    try:
        await cursor.execute(
            """
            SELECT
                rp.id,
                rp.profile_name,
                rp.profession_id,
                rp.department_id,
                rp.role_id,
                p.name AS profession,
                d.name AS department,
                r.name AS specific_role,
                rp.created_at
            FROM role_profiles rp
            LEFT JOIN roles r ON rp.role_id = r.id
            LEFT JOIN departments d ON rp.department_id = d.id
            LEFT JOIN professions p ON rp.profession_id = p.id
            WHERE rp.id = %s
            """,
            (profile_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        return row
    finally:
        await cursor.close()

# --- CONFIG SAVE (Stage 1) ---
from pydantic import Field

class SaveConfigPayload(BaseModel):
    profession: Optional[int]
    department: Optional[int]
    role: Optional[int]
    name: str = Field(..., min_length=1)
    skive: Dict[str, dict]
    day_to_day: Optional[List[str]] = []
    kras: Optional[List[str]] = []

@app.post("/api/config/save")
async def save_config(payload: SaveConfigPayload, conn = Depends(get_db_connection)):
    """Persist a role profile and normalized SKIVE ratings."""
    try:
        cursor = await conn.cursor()
        # Detect role_profiles columns to handle schema drift
        db_name = os.getenv("DB_NAME")
        col_cursor = await conn.cursor(aiomysql.DictCursor)
        await col_cursor.execute(
            """
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = 'role_profiles'
            """,
            (db_name,)
        )
        cols = {row['column_name'] for row in (await col_cursor.fetchall())}
        await col_cursor.close()

        column_names = []
        values = []

        # Name columns
        if 'name' in cols:
            column_names.append('name')
            values.append(payload.name)
        if 'profile_name' in cols:
            column_names.append('profile_name')
            values.append(payload.name)

        # Foreign keys
        column_names += ['profession_id', 'department_id', 'role_id']
        values += [payload.profession, payload.department, payload.role]

        # JSON fields if present and/or NOT NULL in some schemas
        if 'skive' in cols:
            column_names.append('skive')
            values.append(json.dumps(payload.skive or {}))
        if 'day_to_day' in cols:
            column_names.append('day_to_day')
            values.append(json.dumps(payload.day_to_day or []))
        if 'kras' in cols:
            column_names.append('kras')
            values.append(json.dumps(payload.kras or []))

        placeholders = ','.join(['%s'] * len(values))
        col_list = ', '.join(column_names)
        sql = f"INSERT INTO role_profiles ({col_list}) VALUES ({placeholders})"
        try:
            await cursor.execute(sql, tuple(values))
        except Exception as e:
            logging.error(f"Insert role_profiles failed: {e}; SQL={sql}; values={values}")
            raise

        profile_id = cursor.lastrowid

        # Insert SKIVE ratings into normalized table (flatten nested objects and accept numeric leaves)
        ratings_inserted = 0

        # Detect skive_ratings category column name
        skive_cols_cur = await conn.cursor(aiomysql.DictCursor)
        await skive_cols_cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = %s AND table_name = 'skive_ratings'
            """,
            (db_name,)
        )
        skive_cols = {row['column_name'] for row in (await skive_cols_cur.fetchall())}
        await skive_cols_cur.close()
        category_col = 'category' if 'category' in skive_cols else ('dimension' if 'dimension' in skive_cols else 'category')

        for category, subs in (payload.skive or {}).items():
            if not isinstance(subs, dict):
                logging.warning(f"Skipping category {category}: not a dict")
                continue
            async for _ in _async_insert_leaves(cursor, profile_id, category, subs, category_col):
                ratings_inserted += 1

        await conn.commit()
        return {"status": "ok", "profile_id": profile_id, "ratings_inserted": ratings_inserted}
    except Exception as e:
        await conn.rollback()
        logging.error(f"Error saving config: {e}")
        raise HTTPException(status_code=500, detail="Failed to save profile")
    finally:
        if 'cursor' in locals():
            await cursor.close()

def _iter_leaf_entries(prefix_cat: str, obj: dict, parent_key: Optional[str] = None):
    """Yield (subcategory, score, description) for numeric leaves across nested dicts."""
    if obj is None:
        return
    if isinstance(obj, (int, float)):
        yield parent_key or "unknown", float(obj), None
        return
    if isinstance(obj, dict):
        val = obj.get("value", obj.get("score")) if hasattr(obj, "get") else None
        if isinstance(val, (int, float)):
            yield parent_key or "unknown", float(val), obj.get("description")
            return
        for k, v in obj.items():
            if isinstance(v, (int, float)):
                yield k, float(v), None
            elif isinstance(v, dict):
                inner_val = v.get("value", v.get("score")) if hasattr(v, "get") else None
                if isinstance(inner_val, (int, float)):
                    yield k, float(inner_val), v.get("description")
                else:
                    for sub_name, score, desc in _iter_leaf_entries(prefix_cat, v, parent_key=k):
                        yield sub_name, score, desc

async def _async_insert_leaves(cursor, profile_id: int, category: str, subs: dict, category_col: str = 'category'):
    """Async generator to insert leaves and yield once per successful insert."""
    for sub_name, score, desc in _iter_leaf_entries(category, subs):
        try:
            # Build SQL with detected category column
            sql = f"""
                INSERT INTO skive_ratings (profile_id, {category_col}, subcategory, score, description)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE score=VALUES(score), description=VALUES(description)
            """
            await cursor.execute(
                sql,
                (profile_id, category.lower(), sub_name, score, desc)
            )
            yield True
        except Exception as e:
            logging.warning(f"Skipping rating insert for {category}/{sub_name}: {e}")


# --- STAGE 2: SIMULATION OBJECTIVES ---
class ObjectiveItem(BaseModel):
    dimension: str
    subcategory: str
    objective: str
    difficulty: Optional[str] = "medium"

class ObjectivesSavePayload(BaseModel):
    profile_id: int
    items: List[ObjectiveItem]

@app.get("/api/objectives")
async def get_objectives(profile_id: int, conn = Depends(get_db_connection)):
    try:
        cursor = await conn.cursor(aiomysql.DictCursor)
        try:
            # Newer schema
            await cursor.execute(
                """
                SELECT id, profile_id, skive_subcategory, objective_text, difficulty, created_at, updated_at
                FROM role_profile_objectives
                WHERE profile_id=%s
                ORDER BY skive_subcategory
                """,
                (profile_id,)
            )
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                {
                    "id": r["id"],
                    "profile_id": r["profile_id"],
                    "dimension": "",
                    "subcategory": r["skive_subcategory"],
                    "objective": r["objective_text"],
                    "difficulty": r.get("difficulty") or "medium",
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
                for r in rows
            ]
        except Exception as e_new:
            logging.info(f"Falling back to legacy objectives schema due to: {e_new}")
            # Legacy schema: dimension, subcategory, objective
            await cursor.execute(
                """
                SELECT id, profile_id, dimension, subcategory, objective, created_at, updated_at
                FROM role_profile_objectives
                WHERE profile_id=%s
                ORDER BY dimension, subcategory
                """,
                (profile_id,)
            )
            rows = await cursor.fetchall()
            await cursor.close()
            return [
                {
                    "id": r["id"],
                    "profile_id": r["profile_id"],
                    "dimension": r.get("dimension") or "",
                    "subcategory": r["subcategory"],
                    "objective": r["objective"],
                    "difficulty": "medium",  # not present in legacy; default
                    "created_at": r.get("created_at"),
                    "updated_at": r.get("updated_at"),
                }
                for r in rows
            ]
    except Exception as e:
        logging.error(f"Error fetching objectives: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch objectives")

@app.post("/api/objectives/save")
async def save_objectives(payload: ObjectivesSavePayload, conn = Depends(get_db_connection)):
    try:
        cursor = await conn.cursor()
        count = 0
        for it in payload.items:
            # Upsert per profile+subcategory; support legacy column name 'subcategory'
            try:
                await cursor.execute(
                    """
                    DELETE FROM role_profile_objectives
                    WHERE profile_id=%s AND skive_subcategory=%s
                    """,
                    (payload.profile_id, it.subcategory)
                )
                await cursor.execute(
                    """
                    INSERT INTO role_profile_objectives (profile_id, skive_subcategory, objective_text, difficulty)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (payload.profile_id, it.subcategory, it.objective, it.difficulty or "medium")
                )
            except Exception as e:
                logging.warning(f"Using legacy column 'subcategory' for role_profile_objectives due to: {e}")
                await cursor.execute(
                    """
                    DELETE FROM role_profile_objectives
                    WHERE profile_id=%s AND subcategory=%s
                    """,
                    (payload.profile_id, it.subcategory)
                )
                try:
                    # Legacy with objective_text but old subcategory name
                    await cursor.execute(
                        """
                        INSERT INTO role_profile_objectives (profile_id, subcategory, objective_text, difficulty)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (payload.profile_id, it.subcategory, it.objective, it.difficulty or "medium")
                    )
                except Exception as e2:
                    logging.info(f"Falling back to fully legacy objectives schema (dimension, subcategory, objective) due to: {e2}")
                    # Fully legacy: includes dimension and 'objective' column
                    await cursor.execute(
                        """
                        DELETE FROM role_profile_objectives
                        WHERE profile_id=%s AND dimension=%s AND subcategory=%s
                        """,
                        (payload.profile_id, it.dimension, it.subcategory)
                    )
                    await cursor.execute(
                        """
                        INSERT INTO role_profile_objectives (profile_id, dimension, subcategory, objective)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (payload.profile_id, it.dimension, it.subcategory, it.objective)
                    )
            count += 1
        await conn.commit()
        return {"status": "ok", "count": count}
    except Exception as e:
        await conn.rollback()
        logging.error(f"Error saving objectives: {e}")
        raise HTTPException(status_code=500, detail="Failed to save objectives")
    finally:
        if 'cursor' in locals():
            await cursor.close()

class GenerateObjectiveRequest(BaseModel):
    # Accept both snake_case and camelCase from the frontend
    profile_id: Optional[int] = Field(None, alias="profile_id")
    profileId: Optional[int] = Field(None, alias="profileId")
    skive_subcategory: Optional[str] = Field(None, alias="skive_subcategory")
    skiveSubcategory: Optional[str] = Field(None, alias="skiveSubcategory")
    difficulty: Optional[str] = "medium"

@app.post("/api/objectives/generate")
async def generate_objective(req: GenerateObjectiveRequest, conn = Depends(get_db_connection)):
    """Generate a single objective text for a given SKIVE subcategory and difficulty."""
    # Normalize fields from either casing
    profile_id = req.profile_id or req.profileId
    sub = (req.skive_subcategory or req.skiveSubcategory)
    if not profile_id or not sub:
        raise HTTPException(status_code=422, detail="profile_id and skive_subcategory are required")
    # Simple deterministic template; can be enhanced with AI later
    diff = (req.difficulty or "medium").lower()
    target = {"easy": "within 2 weeks", "medium": "within this quarter", "hard": "within 30 days"}.get(diff, "within this quarter")
    obj = f"Improve {sub} performance by implementing 2 focused actions {target} and tracking weekly progress."
    return {"objective": obj, "difficulty": diff}

# --- AI SUGGESTIONS: Day-to-Day and KRAs ---
class RoleKey(BaseModel):
    profession: Optional[int]
    department: Optional[int]
    role: Optional[int]

async def _resolve_role_context(conn, key: RoleKey) -> Dict[str, str]:
    ctx = {"profession": "", "department": "", "role": ""}
    cur = await conn.cursor()
    try:
        if key.profession:
            await cur.execute("SELECT name FROM professions WHERE id=%s", (key.profession,))
            row = await cur.fetchone()
            ctx["profession"] = row[0] if row else ""
        if key.department:
            await cur.execute("SELECT name FROM departments WHERE id=%s", (key.department,))
            row = await cur.fetchone()
            ctx["department"] = row[0] if row else ""
        if key.role:
            await cur.execute("SELECT name FROM roles WHERE id=%s", (key.role,))
            row = await cur.fetchone()
            ctx["role"] = row[0] if row else ""
    finally:
        await cur.close()
    return ctx

def _tokens(*parts: str) -> List[str]:
    return [p.lower() for p in parts if p]

def _is_specific(s: str) -> bool:
    s = s or ""
    return any(ch.isdigit() for ch in s) or any(k in s.lower() for k in ["q", "%", "sla", "tat", "count", "per "])

def _on_topic(s: str, toks: List[str]) -> bool:
    s_low = (s or "").lower()
    return any(t in s_low for t in toks)

def _postprocess(items: List[str], toks: List[str], limit: int, fallback: List[str]) -> List[str]:
    cleaned = []
    for it in items or []:
        it = str(it).strip().strip('"')
        if it and _on_topic(it, toks) and _is_specific(it):
            cleaned.append(it)
    if len(cleaned) < limit:
        need = limit - len(cleaned)
        for it in fallback:
            if it not in cleaned:
                cleaned.append(it)
            if len(cleaned) >= limit:
                break
    return cleaned[:limit]

@app.post("/api/ai/day_to_day")
async def suggest_day_to_day(key: RoleKey, conn = Depends(get_db_connection)):
    ctx = await _resolve_role_context(conn, key)
    profession = ctx.get("profession", ""); department = ctx.get("department", ""); role = ctx.get("role", "")
    toks = _tokens(profession, department, role)

    def deterministic_items() -> List[str]:
        r = role.lower(); d = department.lower()
        base = [
            f"Review {r} queue and triage high-priority items by 10 AM",
            f"Prepare and analyze {r} metrics dashboard; share insights weekly",
            f"Coordinate with {d} stakeholders to clarify requirements and blockers",
            f"Perform peer review/QA on 2 {r} outputs daily",
            f"Document process updates and SOP changes in the team wiki",
            f"Attend stand-up and provide status, risks, and next actions",
            f"Respond to customer/internal queries within SLA",
            f"Identify 1 improvement opportunity and log it to backlog",
        ]
        if "underwrit" in r:
            base[0] = "Review new submissions and prioritize high-value risks before noon"
            base[2] = "Coordinate with brokers and actuarial on pricing/wordings"
        if "claims" in d:
            base[3] = "Perform QA on 5 claim files; ensure documentation completeness"
        return base

    if API_KEY and not DISABLE_AI:
        try:
            prompt = (
                "Generate day-to-day tasks for the role below. Return STRICT JSON with key 'items' as an array of 8 strings.\n"
                f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            text = resp.text if hasattr(resp, "text") else str(resp)
            # naive JSON extract
            try:
                data = json.loads(text)
                items_raw = data.get("items", [])
            except Exception:
                items_raw = []
            items = _postprocess(items_raw, toks, 8, deterministic_items())
            return {"items": items}
        except Exception as e:
            logging.warning("Gemini day_to_day failed, using deterministic: %s", e)
            return {"items": deterministic_items()}
    else:
        return {"items": deterministic_items()}

@app.post("/api/ai/kras")
async def suggest_kras(key: RoleKey, conn = Depends(get_db_connection)):
    ctx = await _resolve_role_context(conn, key)
    profession = ctx.get("profession", ""); department = ctx.get("department", ""); role = ctx.get("role", "")
    toks = _tokens(profession, department, role)

    def deterministic_kras() -> List[str]:
        r = role.lower(); d = department.lower()
        base = [
            f"Achieve ≥ 95% SLA adherence for key {r} processes by Q4",
            f"Reduce defect rate in {r} outputs to < 2% by end of quarter",
            f"Improve data accuracy for {r} reports to ≥ 99.5% each month",
            f"Deliver 2 process improvements per quarter, saving ≥ 5% effort",
            f"Maintain stakeholder NPS ≥ 8.5/10 across {d} counterparts",
            f"Identify and mitigate top 3 operational risks quarterly",
            f"Coach team: 1 enablement session/month; lift junior throughput by 10%",
            f"Publish monthly KPI review with 3 corrective actions and owners",
        ]
        if "claims" in d or "adjudication" in d:
            base[0] = "Process ≥ 95% of claims within SLA; keep average TAT under 48 hours"
            base[1] = "Reduce claim reopens to < 1.5% by implementing QA feedback loops"
        if "underwrit" in r:
            base = [
                "Maintain portfolio loss ratio ≤ 65% for the fiscal year",
                "Grow bound premium by 15% YoY while adhering to risk appetite",
                "Achieve ≥ 95% underwriting file completeness and audit readiness",
                "Reduce referral turnaround time to < 24 hours for 90% of cases",
                "Increase hit ratio to ≥ 25% while sustaining target pricing adequacy",
                "Implement 2 guideline improvements/quarter based on loss analysis",
                "Achieve ≥ 98% policy wording accuracy across bound policies",
                "Lift broker satisfaction to ≥ 8.5/10 via quarterly feedback",
            ]
        if "sales" in d or "business development" in d:
            base[0] = "Increase qualified pipeline by 25% QoQ; maintain win-rate ≥ 20%"
            base[3] = "Launch 1 new outreach playbook/quarter; lift conversion by 10%"
        if "fraud" in r:
            base[5] = "Reduce confirmed fraud loss by 30% YoY through targeted investigations"
        return base

    if API_KEY and not DISABLE_AI:
        try:
            prompt = (
                "Generate SMART KRAs for the role below. Each KRA must include a measurable target and timeframe.\n"
                f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                "Return STRICT JSON with key 'items' as an array of 8 strings."
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            text = resp.text if hasattr(resp, "text") else str(resp)
            try:
                data = json.loads(text)
                items_raw = data.get("items", [])
            except Exception:
                items_raw = []
            items = _postprocess(items_raw, toks, 8, deterministic_kras())
            return {"items": items}
        except Exception as e:
            logging.warning("Gemini kras failed, using deterministic: %s", e)
            return {"items": deterministic_kras()}
    else:
        return {"items": deterministic_kras()}

# --- Compatibility GET endpoints for suggestions used by the frontend ---
@app.get("/api/suggestions/day_to_day/{role_id}")
async def get_day_to_day_suggestions(role_id: int, conn = Depends(get_db_connection)):
    """Compatibility wrapper: generate day-to-day suggestions by role id using Gemini AI.
    Uses the same AI logic as /api/ai/day_to_day but with role_id parameter.
    """
    try:
        # Get role context from database
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT r.title as role, d.name as department, p.name as profession
                FROM roles r
                JOIN departments d ON r.department_id = d.id
                JOIN professions p ON d.profession_id = p.id
                WHERE r.id = %s
            """, (role_id,))
            result = await cur.fetchone()
            
        if not result:
            raise ValueError(f"Role {role_id} not found")
            
        profession = result.get("profession", "")
        department = result.get("department", "")
        role = result.get("role", "")
        toks = _tokens(profession, department, role)

        def deterministic_items() -> List[str]:
            r = role.lower(); d = department.lower()
            base = [
                f"Review priority queue and plan work for the day",
                f"Update metrics and share key insights with {d} team",
                f"Collaborate with stakeholders to unblock issues",
                f"Perform peer review/QA on team outputs",
                f"Document process updates and SOP changes in the team wiki",
                f"Attend stand-up and provide status, risks, and next actions",
                f"Respond to customer/internal queries within SLA",
                f"Identify 1 improvement opportunity and log it to backlog",
            ]
            if "underwrit" in r:
                base[0] = "Review new submissions and prioritize high-value risks before noon"
                base[2] = "Coordinate with brokers and actuarial on pricing/wordings"
            if "claims" in d:
                base[3] = "Perform QA on 5 claim files; ensure documentation completeness"
            return base

        # Use Gemini AI if available, otherwise fallback to deterministic
        if API_KEY and not DISABLE_AI:
            try:
                prompt = (
                    "Generate day-to-day tasks for the role below. Return STRICT JSON with key 'items' as an array of 8 strings.\n"
                    f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                )
                model = genai.GenerativeModel("gemini-1.5-flash")
                resp = await asyncio.to_thread(model.generate_content, prompt)
                text = resp.text if hasattr(resp, "text") else str(resp)
                # naive JSON extract
                try:
                    data = json.loads(text)
                    items_raw = data.get("items", [])
                except Exception:
                    items_raw = []
                items = _postprocess(items_raw, toks, 8, deterministic_items())
                return {"suggestions": items}
            except Exception as e:
                logging.warning("Gemini day_to_day failed, using deterministic: %s", e)
                return {"suggestions": deterministic_items()}
        else:
            return {"suggestions": deterministic_items()}
    except Exception as e:
        logging.warning(f"/api/suggestions/day_to_day/{role_id} failed, using generic defaults: {e}")
        generic = [
            "Review priority queue and plan work for the day",
            "Update metrics and share key insights",
            "Collaborate with stakeholders to unblock issues",
            "Perform peer review/QA on team outputs",
            "Document important changes in the wiki",
            "Attend stand-up and align on next actions",
            "Respond to pending queries within SLA",
            "Identify one improvement and add to backlog",
        ]
        return {"suggestions": generic}

@app.get("/api/suggestions/kras/{role_id}")
async def get_kras_suggestions(role_id: int, conn = Depends(get_db_connection)):
    """Compatibility wrapper: generate KRA suggestions by role id using Gemini AI.
    Uses the same AI logic as /api/ai/kras but with role_id parameter.
    """
    try:
        # Get role context from database
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT r.title as role, d.name as department, p.name as profession
                FROM roles r
                JOIN departments d ON r.department_id = d.id
                JOIN professions p ON d.profession_id = p.id
                WHERE r.id = %s
            """, (role_id,))
            result = await cur.fetchone()
            
        if not result:
            raise ValueError(f"Role {role_id} not found")
            
        profession = result.get("profession", "")
        department = result.get("department", "")
        role = result.get("role", "")
        toks = _tokens(profession, department, role)

        def deterministic_kras() -> List[str]:
            r = role.lower(); d = department.lower()
            base = [
                f"Achieve ≥ 95% SLA adherence for key {r} processes by Q4",
                f"Reduce defect rate in {r} outputs to < 2% by end of quarter",
                f"Improve data accuracy for {r} reports to ≥ 99.5% each month",
                f"Deliver 2 process improvements per quarter, saving ≥ 5% effort",
                f"Maintain stakeholder NPS ≥ 8.5/10 across {d} counterparts",
                f"Identify and mitigate top 3 operational risks quarterly",
                f"Coach team: 1 enablement session/month; lift junior throughput by 10%",
                f"Publish monthly KPI review with 3 corrective actions and owners",
                "Lift broker satisfaction to ≥ 8.5/10 via quarterly feedback",
            ]
            if "sales" in d or "business development" in d:
                base[0] = "Increase qualified pipeline by 25% QoQ; maintain win-rate ≥ 20%"
                base[3] = "Launch 1 new outreach playbook/quarter; lift conversion by 10%"
            if "fraud" in r:
                base[5] = "Deploy 2 new anomaly-detection rules; lower false negatives by 10%"
            return base

        # Use Gemini AI if available, otherwise fallback to deterministic
        if API_KEY and not DISABLE_AI:
            try:
                prompt = (
                    "Generate KRAs (Key Result Areas) for the role below. Return STRICT JSON with key 'items' as an array of 8 strings.\n"
                    f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                )
                model = genai.GenerativeModel("gemini-1.5-flash")
                resp = await asyncio.to_thread(model.generate_content, prompt)
                text = resp.text if hasattr(resp, "text") else str(resp)
                # naive JSON extract
                try:
                    data = json.loads(text)
                    items_raw = data.get("items", [])
                except Exception:
                    items_raw = []
                items = _postprocess(items_raw, toks, 8, deterministic_kras())
                return {"suggestions": items}
            except Exception as e:
                logging.warning("Gemini KRAs failed, using deterministic: %s", e)
                return {"suggestions": deterministic_kras()}
        else:
            return {"suggestions": deterministic_kras()}
    except Exception as e:
        logging.warning(f"/api/suggestions/kras/{role_id} failed, using generic defaults: {e}")
        generic = [
            "Achieve 95% SLA adherence for key processes by Q4",
            "Reduce defect rate in outputs to < 2% by end of quarter",
            "Improve data accuracy for reports to ≥ 99.5% each month",
            "Deliver 2 process improvements per quarter, saving ≥ 5% effort",
            "Maintain stakeholder NPS ≥ 8.5/10 across counterparts",
            "Identify and mitigate top 3 operational risks quarterly",
            "Coach team: 1 enablement session/month; lift junior throughput by 10%",
            "Publish monthly KPI review with 3 corrective actions and owners",
        ]
        return {"suggestions": generic}

@app.get("/api/profile/multi-radar/{profile_id}")
async def get_multi_radar_data(profile_id: int, conn = Depends(get_db_connection)):
    """Get separate radar data for each SKIVE category plus consolidated"""
    try:
        cursor = await conn.cursor(aiomysql.DictCursor)
        # Fetch from role_profiles, not skive_ratings
        await cursor.execute("SELECT * FROM role_profiles WHERE id = %s", (profile_id,))
        profile_row = await cursor.fetchone()
        await cursor.close()

        if not profile_row:
            raise HTTPException(status_code=404, detail="Profile not found")

        ratings = []
        # Prioritize skive JSON column if it exists and is populated
        if profile_row.get('skive'):
            try:
                skive_obj = json.loads(profile_row['skive']) if isinstance(profile_row['skive'], (str, bytes)) else profile_row['skive']
                ratings = _ratings_from_skive_json(skive_obj)
            except (json.JSONDecodeError, TypeError):
                pass # Fallback to wide columns if JSON is invalid

        # Fallback or supplement with wide-format columns
        if not ratings:
            ratings = _ratings_from_wide_profile(profile_row)

        if not ratings:
            raise HTTPException(status_code=404, detail="No SKIVE data found for profile")
        
        # Group by SKIVE category
        categories = {}
        for rating in ratings:
            cat = rating['category'].lower()
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'subcategory': rating['subcategory'],
                'score': float(rating['score'])
            })
        
        # Calculate averages for each category
        category_averages = {}
        individual_radars = {}
        
        for cat, cat_ratings in categories.items():
            # Calculate average for consolidated radar
            avg_score = sum(r['score'] for r in cat_ratings) / len(cat_ratings) if cat_ratings else 0
            category_averages[cat] = avg_score
            
            # Individual radar data for this category
            individual_radars[cat] = {
                'data': cat_ratings,
                'average': avg_score
            }
        
        # Generate dynamic archetypes for each category
        category_archetypes = {}
        for cat in categories.keys():
            # Filter ratings for the current category to pass to the function
            category_specific_ratings = [r for r in ratings if r['category'].lower() == cat.lower()]
            archetype = await generate_dynamic_archetype(category_specific_ratings, cat, conn)
            category_archetypes[cat] = archetype
        
        # Generate consolidated archetype
        consolidated_archetype = await generate_consolidated_archetype(ratings, conn)
        
        return {
            'individual_radars': individual_radars,
            'consolidated_radar': category_averages,
            'category_archetypes': category_archetypes,
            'consolidated_archetype': consolidated_archetype
        }
    except Exception as e:
        logging.error(f"Error getting multi-radar data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _ratings_from_skive_json(skive_obj: dict, filter_category: Optional[str] = None) -> List[Dict]:
    """Flatten skive JSON {category: {sub: score or {value}}} into list of {category, subcategory, score}.
    Accept both numeric leaves and {value, description} leaves.
    Optionally filter to a single category.
    """
    out: List[Dict] = []
    if not isinstance(skive_obj, dict):
        return out
    for cat, subs in skive_obj.items():
        cat_l = str(cat).lower()
        if filter_category and cat_l != str(filter_category).lower():
            continue
        if not isinstance(subs, dict):
            continue
        for sub, val in subs.items():
            score = None
            if isinstance(val, (int, float)):
                score = float(val)
            elif isinstance(val, dict):
                v = val.get('value', val.get('score')) if hasattr(val, 'get') else None
                if isinstance(v, (int, float)):
                    score = float(v)
            if isinstance(score, float):
                out.append({'category': cat_l, 'subcategory': sub, 'score': score})
    return out

def _ratings_from_wide_profile(profile_row: Dict) -> List[Dict]:
    """Transforms SKIVE ratings from a wide role_profiles row to a long-format list."""
    ratings = []
    for col, value in profile_row.items():
        if value is None or not isinstance(value, (int, float)):
            continue
        parts = col.split('_')
        if len(parts) < 2 or parts[0] not in ['skills', 'knowledge', 'identity', 'values', 'ethics']:
            continue
        
        category = parts[0]
        # Re-assemble subcategory, handling camelCase
        subcategory_parts = parts[1:]
        subcategory = subcategory_parts[0] + ''.join(x.title() for x in subcategory_parts[1:])
        
        # Convert camelCase subcategory to readable words
        readable_subcategory = re.sub(r'(?<!^)(?=[A-Z])', ' ', subcategory).title()

        ratings.append({
            'category': category,
            'subcategory': readable_subcategory,
            'score': float(value)
        })
    return ratings

async def generate_consolidated_archetype(all_ratings: List[Dict], conn) -> Dict:
    """Generate overall consolidated archetype across all SKIVE categories"""

    
    if not all_ratings:
        return {'narrative': 'No profile data available', 'signature_competencies': []}
    
    # Identify top signature competencies across all categories
    signature_comps = identify_signature_competencies(all_ratings, top_n=3)

    # Categorize all ratings by proficiency tier
    tiers = categorize_by_proficiency_tier(all_ratings)

    # Build consolidated narrative using phrase library, mirroring the per-category generator
    narrative_parts: List[str] = []

    # Signature narrative parts (use each comp's own category and tier)
    if signature_comps:
        signature_phrases: List[str] = []
        for comp in signature_comps:
            cat = str(comp.get('category', '')).lower()
            sub = comp.get('subcategory', '')
            score = float(comp.get('score', 0))
            tier = get_proficiency_tier(score)
            try:
                cur = await conn.cursor(aiomysql.DictCursor)
                await cur.execute(
                    """SELECT descriptor_phrase FROM competency_descriptors 
                       WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = %s AND narrative_type = 'signature'""",
                    (cat, sub, tier)
                )
                row = await cur.fetchone()
            finally:
                await cur.close()
            if row and row.get('descriptor_phrase'):
                signature_phrases.append(row['descriptor_phrase'])
        if signature_phrases:
            narrative_parts.append(f"This role is defined by mastery of {', '.join(signature_phrases)}.")

    # Supporting narrative: other high-tier (>=8) comps excluding signature
    supporting_phrases: List[str] = []
    for comp in tiers['high']:
        if comp in signature_comps:
            continue
        cat = str(comp.get('category', '')).lower()
        sub = comp.get('subcategory', '')
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(
                """SELECT descriptor_phrase FROM competency_descriptors 
                   WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = 'high' AND narrative_type = 'supporting'""",
                (cat, sub)
            )
            row = await cur.fetchone()
        finally:
            await cur.close()
        if row and row.get('descriptor_phrase'):
            supporting_phrases.append(row['descriptor_phrase'])
    if supporting_phrases:
        narrative_parts.append(f"Supported by {', '.join(supporting_phrases)}.")

    # Foundational narrative: select top few medium-tier comps
    foundational_phrases: List[str] = []
    for comp in tiers['medium'][:3]:
        cat = str(comp.get('category', '')).lower()
        sub = comp.get('subcategory', '')
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(
                """SELECT descriptor_phrase FROM competency_descriptors 
                   WHERE skive_category = %s AND subcategory = %s AND proficiency_tier = 'medium' AND narrative_type = 'foundational'""",
                (cat, sub)
            )
            row = await cur.fetchone()
        finally:
            await cur.close()
        if row and row.get('descriptor_phrase'):
            foundational_phrases.append(row['descriptor_phrase'])
    if foundational_phrases:
        narrative_parts.append(f"Built upon a foundation of {', '.join(foundational_phrases)}.")

    # Category strengths map (list of strong subcategories per SKIVE for UI chips)
    category_strengths: Dict[str, List[str]] = {}
    for rating in all_ratings:
        cat = str(rating.get('category', '')).lower()
        category_strengths.setdefault(cat, [])
        if float(rating.get('score', 0)) >= 8:
            category_strengths[cat].append(rating.get('subcategory', ''))

    return {
        'narrative': ' '.join(narrative_parts) if narrative_parts else 'Balanced professional competence across all SKIVE dimensions.',
        'signature_competencies': [comp.get('subcategory', '') for comp in signature_comps],
        'category_strengths': category_strengths
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
