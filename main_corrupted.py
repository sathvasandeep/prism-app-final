# main.py - FastAPI back-end for the PRISM Framework
# ==================================================

# pip install "fastapi[all]" uvicorn python-dotenv mysql-connector-python google-generativeai "passlib[bcrypt]" "pydantic[email]"


import os
import logging
import json
import asyncio
from typing import Dict, List, Optional
import aiomysql
import google.generativeai as genai
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator
from passlib.context import CryptContext
from contextlib import contextmanager
from routes import core
from routes import config
from dotenv import load_dotenv
from models.phrase_library import (
    CREATE_COMPETENCY_DESCRIPTORS_TABLE,
    COMPETENCY_DESCRIPTORS_SEED_DATA,
    get_proficiency_tier,
    get_narrative_type
)

load_dotenv()  # This line should already be there
print("Current working directory:", os.getcwd())
print("Environment variables:", {k: v for k, v in os.environ.items() if "GEMINI" in k or "DISABLE" in k})

# New imports
from db.database import Base, engine
# from routes.customer import router as customer_router
from routes import customer

# Instantiate the FastAPI app
app = FastAPI()

# Add routers
app.include_router(customer.router, prefix="/api", tags=["Customer"])
app.include_router(core.router, prefix="/api")
app.include_router(config.router)

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
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory DB
user_journey_db = {}

# Request model
class UserSelection(BaseModel):
    user_id: Optional[str] = None  # Optional to allow anonymous start
    user_type: str  # 'student' or 'professional'
    pathway: str  # 'exploration' or 'assessment'
    interest_answers: Optional[List[str]] = []
    results: Optional[dict] = {}

@app.post("/api/save-user-selection")
def save_user_selection(data: UserSelection):
    user_id = data.user_id or str(uuid4())
    user_journey_db[user_id] = {
        "user_type": data.user_type,
        "pathway": data.pathway,
        "interest_answers": data.interest_answers,
        "results": data.results,
        "timestamp": datetime.datetime.now().isoformat()
    }
    return {"status": "success", "user_id": user_id}

# --- 1. SETUP ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")

# --- 2. ENVIRONMENT LOADING ---
API_KEY = os.getenv("GEMINI_API_KEY")
# Default to deterministic outputs unless explicitly enabled
DISABLE_AI = os.getenv("DISABLE_AI", "1") == "1"

if API_KEY and not DISABLE_AI:
    try:
        genai.configure(api_key=API_KEY)
        logging.info("Gemini client configured ")
    except Exception as e:
        logging.error(f"Gemini configure failed: {e}")
        API_KEY = None
else:
    logging.warning("API_KEY missing – AI routes disabled.")

# --- 3. DATABASE HELPER ---
DB_POOL = None

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
                        REFERENCES role_profiles(id) ON DELETE CASCADE
                        """
                    )
                except Exception as fk2_err:
                    logging.warning("Skipping FK on role_profile_objectives due to: %s", fk2_err)
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

# --- 4. FASTAPI APP & CORS SETUP ---
# app = FastAPI(title="PRISM Framework API")
# origins = ["http://localhost", "http://localhost:8080", "http://localhost:5173", "http://127.0.0.1", "http://127.0.0.1:8080", "http://127.0.0.1:5173"]
# app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# app.include_router(auth_router, prefix="/api")


# --- 6. DTOS (DATA TRANSFER OBJECTS) ---
class Profile(BaseModel): id: Optional[int] = None # Placeholder
class UserCreate(BaseModel): email: EmailStr; password: str
class TaskGenerationRequest(BaseModel): competency_id: str; objective_text: str; flavor_id: Optional[str] = None
class TaskResponseIn(BaseModel): response_payload: Dict
class ProfessionOut(BaseModel): id:int; name:str
class DepartmentOut(BaseModel): id:int; name:str
class RoleOut(BaseModel): id:int; name:str

# --- 7. HELPER FUNCTIONS ---
def hash_password(password: str): return pwd_context.hash(password)

# --- 8. STAGE 3 HELPER DICTIONARIES ---
COMPETENCY_TO_GCR_MAP = { "skills-cognitive-decisionMaking": "gcr-ED", "skills-cognitive-strategicPlanning": "gcr-SQ" }
GCR_UI_COMPONENT_MAP = { "gcr-ED": "ui-rank-and-write", "gcr-SQ": "ui-sequence-cards" }
GCR_DEFINITIONS = { "gcr-ED": { "id": "gcr-ED", "name": "Evaluative Decision", "input_schema": { "type": "object", "properties": { "options_list": {"type": "array", "items": {"type": "string"}}, "criteria_md": {"type": "string"}}} }, "gcr-SQ": { "id": "gcr-SQ", "name": "Procedural Sequencing", "input_schema": { "type": "object", "properties": { "scenario_md": {"type": "string"}, "items_to_sequence": { "type": "array", "items": { "type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}}}}}} } }
GCR_FLAVORS = { "gcr-ED": [ {"id": "prioritization", "name": "Prioritization"}, {"id": "resource_allocation", "name": "Resource Allocation"}, {"id": "risk_mitigation", "name": "Risk Mitigation"}, {"id": "ethical_dilemma", "name": "Ethical Dilemma"},], "gcr-SQ": [{"id": "process_workflow", "name": "Process Workflow"}, {"id": "project_timeline", "name": "Project Timeline"}] }

# ====================================================================
# API ENDPOINTS
# ====================================================================

# --- AUTHENTICATION ---
@app.post("/auth/register", response_model=Dict)
async def register_user(user: UserCreate, conn: aiomysql.Connection = Depends(get_db_connection)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="A user with this email already exists.")
        hashed_pw = hash_password(user.password)
        await cur.execute("INSERT INTO users (email, hashed_password, role) VALUES (%s, %s, %s)", (user.email, hashed_pw, 'student'))
        new_user_id = cur.lastrowid
        await cur.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (new_user_id,))
        await conn.commit()
        return {"message": "User registered successfully!", "user_id": new_user_id}

# --- DYNAMIC LOOKUP ---
@app.get("/api/health")
async def healthcheck():
    try:
        # simple pool check
        async with DB_POOL.acquire() as _:
            pass
        return {"status": "ok"}
    except Exception as e:
        logging.exception("Healthcheck failed: %s", e)
        return {"status": "error", "detail": str(e)}

@app.get("/api/professions", response_model=List[ProfessionOut])
async def list_professions(conn: aiomysql.Connection = Depends(get_db_connection)):
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id, name FROM professions ORDER BY name")
            return await cur.fetchall()
    except Exception as e:
        logging.exception("/api/professions failed: %s", e)
        # Return empty list to keep UI functional
        return []

@app.get("/api/departments")
async def list_departments(profession_id: Optional[int] = None, conn: aiomysql.Connection = Depends(get_db_connection)):
    """List departments, optionally filtered by profession via mapping table `department_profession_map`."""
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if profession_id:
                await cur.execute(
                    """
                    SELECT d.id, d.name
                    FROM departments d
                    JOIN department_profession_map m ON m.department_id = d.id
                    WHERE m.profession_id = %s
                    ORDER BY d.name
                    """,
                    (profession_id,),
                )
            else:
                await cur.execute("SELECT id, name FROM departments ORDER BY name")
            return await cur.fetchall()
    except Exception as e:
        logging.exception("/api/departments failed: %s", e)
        return []

@app.get("/api/roles")
async def list_roles(department_id: Optional[int] = None, conn: aiomysql.Connection = Depends(get_db_connection)):
    """List roles, optionally filtered by department via mapping table `role_department_map`."""
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if department_id:
                await cur.execute(
                    """
                    SELECT r.id, r.name
                    FROM roles r
                    JOIN role_department_map m ON m.role_id = r.id
                    WHERE m.department_id = %s
                    ORDER BY r.name
                    """,
                    (department_id,),
                )
            else:
                await cur.execute("SELECT id, name FROM roles ORDER BY name")
            return await cur.fetchall()
    except Exception as e:
        logging.exception("/api/roles failed: %s", e)
        return []

@app.get("/api/kras_master/{role_id}")
async def get_kras_for_role(role_id: int, conn: aiomysql.Connection = Depends(get_db_connection)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id, name, description FROM kras_master WHERE role_id=%s", (role_id,))
        return await cur.fetchall()

# --- SIMULATION DEFINITION (ADMIN) ---
@app.get("/api/simulations")
async def list_simulations(conn: aiomysql.Connection = Depends(get_db_connection)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        try:
            await cur.execute("""
                SELECT 
                    sd.id,
                    r.title as specific_role,
                    p.name as profession,
                    d.name as department,
                    sd.updated_at,
                    sd.archetype
                FROM simulation_definitions sd
                JOIN roles r ON sd.professional_role_id = r.id
                JOIN departments d ON r.department_id = d.id
                JOIN professions p ON d.profession_id = p.id
                ORDER BY sd.updated_at DESC
            """)
            rows = await cur.fetchall()
            return rows
        except Exception as err:
            logging.error(f"DB error in list_simulations: {err}")
            raise HTTPException(status_code=500, detail="Database query failed.")

# --- TASK GENERATION, SUBMISSION, EVALUATION ---
# (Endpoints for task generation, submission, and evaluation would go here)
# For now, they are omitted to focus on getting the server to start.

# --- CONFIG SAVE ---
class SaveConfigPayload(BaseModel):
    profession: Optional[int]
    department: Optional[int]
    role: Optional[int]
    # Name must be provided and non-blank after trimming
    name: str = Field(..., min_length=1, description="Profile name is required")
    skive: Dict[str, Any]
    day_to_day: List[str]
    kras: List[str]

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Profile name is required and cannot be blank")
        return str(v).strip()

@app.post("/api/config/save")
async def save_config(payload: SaveConfigPayload, conn: aiomysql.Connection = Depends(get_db_connection)):
    """Persist a role profile configuration."""
    async with conn.cursor(aiomysql.DictCursor) as cur:
        try:
            # Determine available columns for profile name and insert accordingly
            await cur.execute(
                """
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'role_profiles' AND COLUMN_NAME IN ('name','profile_name')
                """,
                (DB_NAME,),
            )
            cols = {row["COLUMN_NAME"] for row in await cur.fetchall()}

            name_columns = []
            if "name" in cols:
                name_columns.append("name")
            if "profile_name" in cols:
                name_columns.append("profile_name")

            # Base columns always present in our schema
            base_cols = ["profession_id", "department_id", "role_id", "skive", "day_to_day", "kras"]

            # Build dynamic column list and values
            insert_cols = ["profession_id", "department_id", "role_id"] + name_columns + ["skive", "day_to_day", "kras"]
            placeholders = ", ".join(["%s"] * len(insert_cols))
            insert_sql = f"INSERT INTO role_profiles ({', '.join(insert_cols)}) VALUES ({placeholders})"

            values = [
                payload.profession,
                payload.department,
                payload.role,
            ]
            # Add one value for each name column present
            for _ in name_columns:
                values.append(payload.name)
            values.extend([
                json.dumps(payload.skive),
                json.dumps(payload.day_to_day),
                json.dumps(payload.kras),
            ])

            await cur.execute(insert_sql, tuple(values))
            profile_id = cur.lastrowid

            # Populate normalized ratings table
            rows = []
            try:
                for category, subs in (payload.skive or {}).items():
                    if isinstance(subs, dict):
                        for sub, score in subs.items():
                            # coerce to int within 1..10
                            try:
                                sval = int(score)
                            except Exception:
                                sval = None
                            if sval is None:
                                continue
                            rows.append((profile_id, str(category), str(sub), max(1, min(10, sval))))
            except Exception as parse_err:
                logging.warning("Failed parsing SKIVE for normalization: %s", parse_err)

            if rows:
                # ensure idempotency: remove existing rows for this profile then bulk insert
                await cur.execute("DELETE FROM role_profile_skive_ratings WHERE profile_id = %s", (profile_id,))
                await cur.executemany(
                    """
                    INSERT INTO role_profile_skive_ratings (profile_id, category, subcategory, score)
                    VALUES (%s, %s, %s, %s)
                    """,
                    rows,
                )

            return {"status": "ok", "profile_id": profile_id, "ratings_inserted": len(rows)}
        except Exception as err:
            logging.exception("Failed to save config: %s", err)
            # Surface error detail in dev to help debugging
            raise HTTPException(status_code=500, detail=f"Failed to save configuration: {err}")

# --- STAGE 2: SIMULATION OBJECTIVES ---
class ObjectiveItem(BaseModel):
    dimension: str  # one of: skills, knowledge, identity, values, ethics
    subcategory: str
    objective: str

class ObjectivesSavePayload(BaseModel):
    profile_id: int
    items: List[ObjectiveItem]

class GenerateObjectiveRequest(BaseModel):
    # Either pass profile_id to look up stored D2D/KRAs, or inline arrays
    profile_id: Optional[int] = None
    role_id: Optional[int] = None
    dimension: str
    subcategory: str
    day_to_day: Optional[List[str]] = None
    kras: Optional[List[str]] = None
    # Optional difficulty level to influence AI objective complexity
    difficulty: Optional[str] = None  # expected: Beginner | Intermediate | Advanced

def _compose_objective_prompt(ctx: Dict[str, str], dimension: str, subcategory: str, tasks: List[str], kras: List[str], difficulty: Optional[str] = None) -> str:
    role = ctx.get("role") or "Role"
    department = ctx.get("department") or "Department"
    profession = ctx.get("profession") or "Profession"
    tasks_block = "\n".join([f"- {t}" for t in tasks[:10]]) if tasks else "Not provided."
    kras_block = "\n".join([f"- {k}" for k in kras[:10]]) if kras else "Not provided."
    diff = (difficulty or "").strip() or "Intermediate"
    return (
        "For a professional role below, generate one concise SMART learning objective suitable for a serious game simulation.\n"
        f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
        f"SKIVE Dimension: {dimension}\nSub-Competency: {subcategory}\nDifficulty Level: {diff}\n"
        "Context: Use the following to make the objective highly relevant and practical.\n"
        f"Key Responsibilities/KRAs:\n{kras_block}\n"
        f"Typical Day-to-Day Tasks:\n{tasks_block}\n\n"
        "Constraints: The objective must be a single sentence, measurable (include %, count, time, or SLA), and realistic for a one-week simulation sprint."
        " Adjust complexity to the Difficulty Level (Beginner: foundational concepts and simpler metrics; Intermediate: moderate complexity and realistic targets; Advanced: specialized/nuanced context and tighter targets)."
        " Return STRICT JSON: {\"text\": \"...\"}."
    )

def _deterministic_objective(dimension: str, subcategory: str, ctx: Dict[str, str]) -> str:
    role = (ctx.get("role") or "role").lower()
    base = f"By end of the sprint, demonstrate {subcategory.lower()} within {dimension} by completing 3 role-accurate scenarios for the {role}, achieving ≥ 90% task accuracy and documenting 2 improvements."
    return base

def _extract_ai_text(raw: str) -> str:
    """Extract a single objective string from a Gemini response that may include code fences or JSON."""
    if raw is None:
        return ""
    text = str(raw).strip()
    # Strip leading code fence
    if text.startswith("```"):
        # drop the first line (``` or ```json)
        text = text.split("\n", 1)[1] if "\n" in text else ""
        # strip trailing fence
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    # Try direct JSON parse
    try:
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("text"), str):
            return data["text"].strip()
    except Exception:
        pass
    # Try to extract JSON object substring if present within fences or prose
    if "{" in raw and "}" in raw:
        candidate = raw[raw.find("{"): raw.rfind("}") + 1]
        try:
            data2 = json.loads(candidate)
            if isinstance(data2, dict) and isinstance(data2.get("text"), str):
                return data2["text"].strip()
        except Exception:
            pass
    # Fallback to first non-empty line that is not a fence
    for ln in str(raw).splitlines():
        s = ln.strip()
        if not s or s.startswith("```"):
            continue
        return s
    return text.strip()

@app.get("/api/objectives")
async def get_objectives(profile_id: int, conn: aiomysql.Connection = Depends(get_db_connection)):
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "SELECT id, profile_id, dimension, subcategory, objective, created_at, updated_at FROM role_profile_objectives WHERE profile_id=%s ORDER BY dimension, subcategory",
            (profile_id,),
        )
        return await cur.fetchall()

@app.post("/api/objectives/save")
async def save_objectives(payload: ObjectivesSavePayload, conn: aiomysql.Connection = Depends(get_db_connection)):
    if not payload.items:
        return {"status": "ok", "inserted": 0}
    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Upsert by (profile_id, dimension, subcategory)
        for it in payload.items:
            try:
                await cur.execute(
                    """
                    INSERT INTO role_profile_objectives (profile_id, dimension, subcategory, objective)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE objective=VALUES(objective), updated_at=CURRENT_TIMESTAMP
                    """,
                    (payload.profile_id, it.dimension, it.subcategory, it.objective),
                )
            except Exception:
                # If no unique key exists, emulate upsert
                await cur.execute(
                    "DELETE FROM role_profile_objectives WHERE profile_id=%s AND dimension=%s AND subcategory=%s",
                    (payload.profile_id, it.dimension, it.subcategory),
                )
                await cur.execute(
                    "INSERT INTO role_profile_objectives (profile_id, dimension, subcategory, objective) VALUES (%s, %s, %s, %s)",
                    (payload.profile_id, it.dimension, it.subcategory, it.objective),
                )
        await conn.commit()
        return {"status": "ok", "count": len(payload.items)}

@app.post("/api/objectives/generate")
async def generate_objective(req: GenerateObjectiveRequest, conn: aiomysql.Connection = Depends(get_db_connection)):
    # Resolve role context via role_id if provided
    ctx = {"profession": None, "department": None, "role": None}
    if req.role_id:
        try:
            ctx = await _get_role_context(conn, RoleKey(role_id=req.role_id))
        except Exception:
            pass

    # Use provided arrays or try to resolve from role_profile if profile_id is given
    tasks: List[str] = req.day_to_day or []
    kras: List[str] = req.kras or []
    if req.profile_id and (not tasks or not kras):
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT day_to_day, kras FROM role_profiles WHERE id=%s", (req.profile_id,))
            row = await cur.fetchone()
            if row:
                try:
                    tasks = tasks or json.loads(row.get("day_to_day") or "[]")
                except Exception:
                    tasks = tasks or []
                try:
                    kras = kras or json.loads(row.get("kras") or "[]")
                except Exception:
                    kras = kras or []

    # Compose prompt and call AI
    if API_KEY and not DISABLE_AI:
        try:
            prompt = _compose_objective_prompt(ctx, req.dimension, req.subcategory, tasks, kras, req.difficulty)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            raw_text = resp.text if hasattr(resp, "text") else str(resp)
            cleaned = _extract_ai_text(raw_text)
            if cleaned:
                return {"text": cleaned}
        except Exception as e:
            logging.warning("Gemini objective failed, using deterministic: %s", e)

    # Deterministic fallback
    return {"text": _deterministic_objective(req.dimension, req.subcategory, ctx)}

# Helper endpoint to verify normalized SKIVE ratings per profile
@app.get("/api/profile/{profile_id}/skive_ratings")
async def get_profile_skive_ratings(profile_id: int, conn: aiomysql.Connection = Depends(get_db_connection)):
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT category, subcategory, score
                FROM role_profile_skive_ratings
                WHERE profile_id = %s
                ORDER BY category, subcategory
                """,
                (profile_id,),
            )
            return await cur.fetchall()
    except Exception as e:
        logging.exception("/api/profile/{profile_id}/skive_ratings failed: %s", e)
        return []

# --- STAGE 3: PROFILE SUMMARY & ARCHETYPES ---

# Seed archetype definitions (can be moved to DB later)
ARCHETYPE_DEFS = [
    {
        "name": "Analytical Strategist",
        "description": "Data-driven decision maker with strong analytical and strategic thinking capabilities",
        "dominant": ["Skills-Cognitive", "Knowledge-Conceptual"],
        "supporting": ["Identity-Problem Solver", "Values-Objectivity"],
        "examples": ["Management Consultant", "Financial Analyst", "Research Director"],
    },
    {
        "name": "Empathetic People Leader",
        "description": "Human-centered leader focused on team development and collaborative success",
        "dominant": ["Skills-Interpersonal", "Identity-Mentor", "Values-Team Wellbeing"],
        "supporting": ["Knowledge-Organisational", "Ethics-Relational"],
        "examples": ["Team Manager", "HR Leader", "Executive Coach"],
    },
    {
        "name": "Technical Virtuoso",
        "description": "Domain expert with deep technical skills and precision-focused approach",
        "dominant": ["Skills-Psychomotor", "Knowledge-Procedural"],
        "supporting": ["Identity-Specialist", "Values-Mastery"],
        "examples": ["Master Surgeon", "Elite Programmer", "Research Scientist"],
    },
    {
        "name": "Ethical Guardian",
        "description": "Principles-driven professional focused on integrity and moral reasoning",
        "dominant": ["Ethics-All", "Values-Integrity", "Knowledge-Regulatory"],
        "supporting": ["Skills-Critical Evaluation", "Skills-Communication"],
        "examples": ["Judge", "Compliance Officer", "Ethics Consultant"],
    },
]

@app.get("/api/archetypes/definitions")
async def archetype_definitions():
    return ARCHETYPE_DEFS

def _skive_key_to_token(category: str, subcategory: str) -> str:
    c = (category or "").strip().lower()
    s = (subcategory or "").strip().lower()
    # Normalize to Title-Case prefixed tokens
    if c == "skills":
        # Map some common groups
        if "cogn" in s or "decision" in s or "strategy" in s:
            return "Skills-Cognitive"
        if "interpersonal" in s or "communicat" in s or "collab" in s:
            return "Skills-Interpersonal"
        if "psychomotor" in s or "technical" in s or "procedur" in s:
            return "Skills-Psychomotor"
        if "critical" in s or "evaluation" in s:
            return "Skills-Critical Evaluation"
        return "Skills-Other"
    if c == "knowledge":
        if "concept" in s or "theoretical" in s:
            return "Knowledge-Conceptual"
        if "procedur" in s or "practical" in s or "applied" in s:
            return "Knowledge-Procedural"
        if "regulator" in s or "policy" in s or "compliance" in s:
            return "Knowledge-Regulatory"
        if "organis" in s or "organiz" in s:
            return "Knowledge-Organisational"
        return "Knowledge-Other"
    if c == "identity":
        if "mentor" in s:
            return "Identity-Mentor"
        if "problem" in s or "solver" in s:
            return "Identity-Problem Solver"
        if "specialist" in s:
            return "Identity-Specialist"
        return "Identity-Other"
    if c == "values":
        if "integrity" in s:
            return "Values-Integrity"
        if "team" in s or "wellbeing" in s:
            return "Values-Team Wellbeing"
        if "objectiv" in s:
            return "Values-Objectivity"
        if "mastery" in s:
            return "Values-Mastery"
        return "Values-Other"
    if c == "ethics":
        if "relat" in s:
            return "Ethics-Relational"
        return "Ethics-All"
    return "Other"

def _deterministic_archetype_scores(tokens: List[str], d2d: List[str], kras: List[str]) -> List[Dict[str, Any]]:
    # Simple weighted match: dominant=2, supporting=1, plus small keyword boost
    token_set = set(tokens)
    text_blob = " \n".join((d2d or []) + (kras or [])).lower()
    kw = {
        "analysis": 0.2, "analytics": 0.2, "strategy": 0.2, "risk": 0.2,
        "stakeholder": 0.15, "mentoring": 0.15, "coach": 0.15,
        "procedure": 0.15, "precision": 0.15, "audit": 0.15,
        "integrity": 0.25, "compliance": 0.25, "ethic": 0.25,
    }
    results = []
    for a in ARCHETYPE_DEFS:
        score = 0.0
        score += sum(2.0 for t in a.get("dominant", []) if t in token_set)
        score += sum(1.0 for t in a.get("supporting", []) if t in token_set)
        score += sum(w for k, w in kw.items() if k in text_blob)
        results.append({"name": a["name"], "score": score, "description": a["description"], "examples": a["examples"]})
    # Normalize
    max_s = max((r["score"] for r in results), default=1.0)
    for r in results:
        r["score"] = round(r["score"] / (max_s or 1.0), 3)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]

@app.get("/api/archetypes/suggest")
async def suggest_archetypes(profile_id: int, conn: aiomysql.Connection = Depends(get_db_connection)):
    # Load SKIVE ratings
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "SELECT category, subcategory, score FROM role_profile_skive_ratings WHERE profile_id=%s",
            (profile_id,),
        )
        ratings = await cur.fetchall()
        # Only select columns that exist in current schema
        await cur.execute(
            "SELECT day_to_day, kras, profession_id, department_id, role_id FROM role_profiles WHERE id=%s",
            (profile_id,),
        )
        prof = await cur.fetchone()
    d2d = []
    kras = []
    try:
        d2d = json.loads((prof or {}).get("day_to_day") or "[]")
    except Exception:
        d2d = []
    try:
        kras = json.loads((prof or {}).get("kras") or "[]")
    except Exception:
        kras = []

    # Build tokens from SKIVE
    tokens: List[str] = []
    for r in ratings or []:
        tokens.append(_skive_key_to_token(r.get("category"), r.get("subcategory")))

    # Prefer Gemini if available for scalable inference
    if API_KEY and not DISABLE_AI:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "You are mapping a professional profile to archetypes.\n"
                f"Archetype catalog (JSON): {json.dumps(ARCHETYPE_DEFS)}\n"
                f"SKIVE tokens: {json.dumps(tokens)}\n"
                f"Day-to-Day items: {json.dumps(d2d[:10])}\n"
                f"KRAs: {json.dumps(kras[:10])}\n"
                "Return STRICT JSON with key 'archetypes' as an array of up to 3 items, each: {name, score: 0..1, rationale, description, examples}."
                " Score reflects fit based on dominant/supporting mappings and evidence in tasks/KRAs."
            )
            resp = await asyncio.to_thread(model.generate_content, prompt)
            raw_text = resp.text if hasattr(resp, "text") else str(resp)
            # Minimal robust parsing
            try:
                data = json.loads(_extract_ai_text(raw_text))
            except Exception:
                # Try extract JSON object/array from raw
                data = {}
                if "[" in raw_text and "]" in raw_text:
                    data = {"archetypes": json.loads(raw_text[raw_text.find("["): raw_text.rfind("]") + 1])}
            items = data.get("archetypes") if isinstance(data, dict) else None
            if isinstance(items, list) and items:
                # sanitize
                out = []
                for it in items[:3]:
                    out.append({
                        "name": str(it.get("name", "")).strip(),
                        "score": float(it.get("score", 0)),
                        "rationale": str(it.get("rationale", "")).strip(),
                        "description": str(it.get("description", "")).strip(),
                        "examples": it.get("examples") or [],
                    })
                logging.info("Gemini archetypes: using AI output (profile_id=%s)", profile_id)
                return {"archetypes": out, "source": "ai"}
        except Exception as e:
            logging.warning("Gemini archetypes failed, using deterministic: %s", e)

    # Deterministic fallback
    det = _deterministic_archetype_scores(tokens, d2d, kras)
    for r in det:
        r["rationale"] = "Matched dominant/supporting tokens and keywords across tasks/KRAs."
    logging.info("Gemini archetypes unavailable -> using deterministic (profile_id=%s)", profile_id)
    return {"archetypes": det, "source": "deterministic"}

@app.get("/api/profile/summary")
async def profile_summary(profile_id: int, conn: aiomysql.Connection = Depends(get_db_connection)):
    # Load core profile bits
    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Use actual column names stored by save_config
        await cur.execute(
            "SELECT profession_id, department_id, role_id, day_to_day, kras FROM role_profiles WHERE id=%s",
            (profile_id,),
        )
        prof = await cur.fetchone()
        if not prof:
            raise HTTPException(status_code=404, detail="Profile not found")
        await cur.execute(
            "SELECT category, subcategory, score FROM role_profile_skive_ratings WHERE profile_id=%s",
            (profile_id,),
        )
        ratings = await cur.fetchall()
    d2d = []
    kras = []
    try:
        d2d = json.loads((prof or {}).get("day_to_day") or "[]")
    except Exception:
        pass
    try:
        kras = json.loads((prof or {}).get("kras") or "[]")
    except Exception:
        pass

    # Archetypes (reuse suggest endpoint logic directly)
    arch = await suggest_archetypes(profile_id, conn)
    arch_source = arch.get("source", "deterministic")

    # Sanitize ratings for JSON serialization (e.g., Decimal -> float)
    ratings_sanitized = []
    for r in ratings:
        try:
            ratings_sanitized.append({
                "category": str(r.get("category", "")),
                "score": float(r.get("score", 0)),
            })
        except Exception:
            continue

    # Compute SKIVE category averages (1–10 scale) for a single source of truth
    bucket = {}
    for r in ratings_sanitized:
        key = (r.get("category") or "").strip().lower()
        if key:
            if key not in bucket:
                bucket[key] = {"sum": 0.0, "n": 0}
            bucket[key]["sum"] += float(r.get("score") or 0.0)
            bucket[key]["n"] += 1
    order = ["skills", "knowledge", "identity", "values", "ethics"]
    skive_averages = []
    for k in order:
        if k in bucket and bucket[k]["n"] > 0:
            avg10 = bucket[k]["sum"] / bucket[k]["n"]
        else:
            avg10 = 0.0
        skive_averages.append({"key": k, "avg10": max(0.0, min(10.0, avg10))})

    # Resolve human-readable role context
    try:
        role_ctx = await _get_role_context(
            conn,
            RoleKey(
                role_id=prof.get("role_id"),
                department_id=prof.get("department_id"),
                profession_id=prof.get("profession_id"),
            ),
        )
    except Exception:
        role_ctx = {"profession": None, "department": None, "role": None}

    # Pathway + snapshot using Gemini when possible
    pathway = {}
    snapshot = {}
    comp = {"band": None, "perks": []}
    summary_source = "deterministic"
    media = {"videos": []}
    if API_KEY and not DISABLE_AI:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "Create a concise profile summary with these sections: pathway, snapshot, compensation.\n"
                f"Profession: {role_ctx.get('profession')}\nDepartment: {role_ctx.get('department')}\nRole: {role_ctx.get('role')}\n"
                f"Day-to-Day (sample): {json.dumps(d2d[:8])}\nKRAs (sample): {json.dumps(kras[:8])}\n"
                f"SKIVE ratings: {json.dumps(ratings_sanitized)}\n"
                "Return STRICT JSON: {\n  'pathway': { 'timeToRole': 'e.g., 3–5 years', 'education': ['Bachelors in ...'], 'certifications': ['...'] },\n"
                "  'snapshot': { 'dayInLife': '2-3 sentences', 'highlights': ['...'], 'lowlights': ['...'], 'difficulty': { 'personal': '...', 'professional': '...' } },\n"
                "  'compensation': { 'band': 'range string', 'perks': ['...'] }\n}\n"
                "Be realistic, role-appropriate, and avoid hallucinating region-specific salaries if unknown—prefer generic ranges."
            )
            logging.info("Gemini profile summary: attempting AI generation (profile_id=%s)", profile_id)
            resp = await asyncio.to_thread(model.generate_content, prompt)
            raw = resp.text if hasattr(resp, "text") else str(resp)
            data = {}
            try:
                data = json.loads(_extract_ai_text(raw))
            except Exception:
                pass
            pathway = data.get("pathway") or {}
            snapshot = data.get("snapshot") or {}
            comp = data.get("compensation") or comp
            if pathway or snapshot or (comp and comp.get("band")):
                summary_source = "ai"
                logging.info("Gemini profile summary: using AI output (profile_id=%s)", profile_id)
        except Exception as e:
            logging.warning("Gemini profile summary failed, using minimal deterministic: %s", e)

    # Minimal deterministic placeholders if AI not available or failed
    if not pathway:
        pathway = {"timeToRole": "3–5 years", "education": ["Bachelor's relevant to role"], "certifications": []}
    if not snapshot:
        snapshot = {
            "dayInLife": "Blend of core responsibilities and stakeholder interactions based on listed tasks and KRAs.",
            "highlights": ["Clear impact on outcomes", "Growth in core competencies"],
            "lowlights": ["Periodic deadline pressure"],
            "difficulty": {"personal": "Moderate", "professional": "Moderate"},
        }
    if not comp.get("band"):
        comp["band"] = "Competitive market range"
        comp["perks"] = comp.get("perks") or ["Health benefits", "Learning budget"]

    return {
        "archetypes": arch.get("archetypes", []),
        "pathway": pathway,
        "snapshot": snapshot,
        "compensation": comp,
        "media": media,
        "skiveRatings": ratings_sanitized,
        "skiveAverages": skive_averages,
        "role": role_ctx,
        "meta": {
            "archetypesSource": arch_source,
            "summarySource": summary_source,
            "aiDisabled": bool(DISABLE_AI),
        },
    }

# --- AI SUGGESTIONS (Mock, no external API calls) ---
class RoleKey(BaseModel):
    profession_id: Optional[int] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None

async def _get_role_context(conn: aiomysql.Connection, key: RoleKey) -> Dict[str, Optional[str]]:
    """Lookup human-readable names for the provided IDs. Falls back gracefully."""
    ctx: Dict[str, Optional[str]] = {"profession": None, "department": None, "role": None}
    async with conn.cursor(aiomysql.DictCursor) as cur:
        if key.role_id:
            # Resolve via mapping tables to be compatible with current schema
            # roles -> role_department_map -> departments -> department_profession_map -> professions
            await cur.execute(
                """
                SELECT
                    COALESCE(r.name, r.title)       AS role,
                    d.name                           AS department,
                    p.name                           AS profession
                FROM roles r
                LEFT JOIN role_department_map rdm       ON rdm.role_id = r.id
                LEFT JOIN departments d                  ON d.id = rdm.department_id
                LEFT JOIN department_profession_map dpm  ON dpm.department_id = d.id
                LEFT JOIN professions p                  ON p.id = dpm.profession_id
                WHERE r.id = %s
                LIMIT 1
                """,
                (key.role_id,),
            )
            row = await cur.fetchone()
            if row and any(row.values()):
                # Return if we could resolve at least one label
                return row
        if key.department_id:
            await cur.execute("SELECT name FROM departments WHERE id=%s", (key.department_id,))
            dep = await cur.fetchone()
            ctx["department"] = dep["name"] if dep else None
        if key.profession_id:
            await cur.execute("SELECT name FROM professions WHERE id=%s", (key.profession_id,))
            prof = await cur.fetchone()
            ctx["profession"] = prof["name"] if prof else None
    return ctx

@app.post("/api/ai/day_to_day")
async def suggest_day_to_day(key: RoleKey, conn: aiomysql.Connection = Depends(get_db_connection)):
    # Get role context from database
    ctx = await _get_role_context(conn, key)
    # Normalize None -> "" to avoid attribute errors downstream
    profession = (ctx.get("profession") or "")
    department = (ctx.get("department") or "")
    role = (ctx.get("role") or "")
    
    # Debug logging
    print(f"\n=== AI Generation Context ===")
    print(f"Profession: {profession}")
    print(f"Department: {department}")
    print(f"Role: {role}")
    print("===========================\n")
    # Note: earlier prototype AI call removed (it referenced undefined DAY_TO_DAY_PROMPT).
    # We use the robust AI block below with deterministic fallback.

    # Helpers
    def _extract_items_from_text(text: str) -> List[str]:
        # Strip common code fences
        t = text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1] if "\n" in t else t
            if t.endswith("```"):
                t = t.rsplit("```", 1)[0]
        # Try JSON
        try:
            data = json.loads(t)
            # Handle multiple possible shapes/keys
            if isinstance(data, dict):
                for k in ["items", "suggestions", "tasks", "day_to_day", "kras"]:
                    if isinstance(data.get(k), list):
                        return [str(x).strip() for x in data.get(k, [])]
            elif isinstance(data, list):
                return [str(x).strip() for x in data]
        except json.JSONDecodeError:
            pass
        except Exception:
            # Any other parsing issue – fall back to line-based parsing
            pass
        # Fallback: split by lines/bullets
        lines = []
        for line in t.split("\n"):
            s = line.strip()
            if not s:
                continue
            # Remove common bullet prefixes
            for prefix in ["- ", "* ", "• "]:
                if s.startswith(prefix):
                    s = s[len(prefix):].strip()
                    break
            lines.append(s)
        return lines

    def _tokens(*parts: str) -> List[str]:
        raw = " ".join([p for p in parts if p])
        toks = set()
        for w in raw.lower().replace("/", " ").replace("&", " ").split():
            if len(w) >= 4:
                toks.add(w)
        # Expand domain stems
        exp = set()
        for k in list(toks):
            if "claim" in k: exp.update(["claim", "adjudicat", "settlement"]) 
            if "fraud" in k: exp.update(["fraud", "investigat", "anti-fraud"]) 
            if "underwrit" in k: exp.update(["underwrit", "risk", "policy"]) 
            if "sales" in k or "business" in k: exp.update(["sales", "pipeline", "revenue", "crm"]) 
        toks.update(exp)
        return list(toks)

    def _is_specific(s: str) -> bool:
        s_low = s.lower()
        has_metric = any(x in s_low for x in ["%", ">=", "<=", "< ", "> ", " per ", " by ", " within ", "tat", "sla", "hours", "hour", "daily", "weekly", "monthly", "q1", "q2", "q3", "q4", "quarter", "target"])
        has_number = any(ch.isdigit() for ch in s)
        return has_metric or has_number

    def _on_topic(s: str, toks: List[str]) -> bool:
        s_low = s.lower()
        return any(t in s_low for t in toks)

    def _postprocess(items: List[str], toks: List[str], limit: int, fallback: List[str]) -> List[str]:
        cleaned = []
        for it in items:
            it = str(it).strip().strip('"')
            if not it:
                continue
            if _on_topic(it, toks) and _is_specific(it):
                cleaned.append(it)
        if len(cleaned) < limit:
            # top-up with deterministic
            need = limit - len(cleaned)
            for it in fallback:
                if it not in cleaned:
                    cleaned.append(it)
                if len(cleaned) >= limit:
                    break
        return cleaned[:limit]

    # Fallback deterministic templates by department/role
    def deterministic_items() -> list[str]:
        r = (role or "").lower()
        d = (department or "").lower()
        p = (profession or "").lower()
        base = [
            f"Pull previous-day {r} KPI dashboard by 09:30 and log 3 anomalies in tracker",
            f"Process and close at least 8 {r} cases/tickets before 14:00 with SLA notes",
            f"Call/meet 3 stakeholders from {d} to unblock high-priority items",
            f"Update SOP/checklist section relevant to {p}-{d}-{r} with 1 concrete improvement",
            f"Perform quality review on 5 random {r} records; record defects with evidence",
            f"Prepare a 5-bullet daily summary on {r} outcomes and share by 17:30",
            f"Identify 1 process risk and propose a mitigation step to the {d} lead",
            f"Mentor a junior on one {r} workflow for 20 minutes with hands-on example",
            f"Reconcile 2 data discrepancies between source system and report; document fix",
            f"Plan next-day top 3 priorities aligned to weekly {r} targets",
        ]
        # Department/role specific tweaks
        if "claims" in d or "adjudication" in d:
            base[1] = "Adjudicate 10 claims with < 2% rework; document 1 complex case rationale"
            base[4] = "Perform QA on 10 claims; report defect rate and top 2 error types"
        if "underwrit" in r:
            base = [
                "Review 12 new submissions; produce underwriting notes and indicative terms by 16:00",
                "Assess risk factors (LOB, sum insured, loss history) for 8 quotes; record rating rationale",
                "Run pricing model for 6 policies; keep target loss ratio ≤ 65%; flag outliers",
                "Refer 2 borderline risks to reinsurance; document facultative/ treaty considerations",
                "Perform peer review on 5 bound policies; ensure wording and endorsements align to appetite",
                "Meet brokers/agents on 3 in-flight deals; negotiate terms and capture next steps in CRM",
                "Update underwriting guidelines with 1 improvement based on recent loss trend",
                "Clear 90% of referrals within SLA (24h); log exceptions with reasons",
                "Validate KYC and compliance checks on 10 submissions; document deviations",
                "Prepare daily bind report and pipeline status by 17:30",
            ]
        if "sales" in d or "business development" in d:
            base[1] = "Make 12 qualified outreach calls and book 2 demos; log in CRM"
            base[2] = "Meet 2 cross-functional partners to progress 1 pipeline deal"
        if "fraud" in r:
            base[0] = "Run fraud detection report by 09:30; open 3 investigations over threshold"
        return base

    # Build topic tokens once
    topic_tokens = _tokens(profession, department, role)

    if API_KEY and not DISABLE_AI:
        try:
            prompt = (
                "You are an assistant generating SPECIFIC, MEASURABLE day-to-day tasks for the EXACT role context.\n"
                f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                "Return STRICT JSON with a top-level key 'items' (array of 10 strings).\n"
                "Hard constraints: items must be ON-TOPIC to the role, include numbers/%/timeframes (SMART), and avoid unrelated domains."
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            text = resp.text if hasattr(resp, "text") else str(resp)
            items_raw = _extract_items_from_text(text)
            processed = _postprocess(items_raw, topic_tokens, 10, deterministic_items())
            return {"items": processed}
        except Exception as e:
            logging.warning("Gemini day_to_day failed, using deterministic: %s", e)
            return {"items": deterministic_items()}
    else:
        return {"items": deterministic_items()}

@app.post("/api/ai/kras")
async def suggest_kras(key: RoleKey, conn: aiomysql.Connection = Depends(get_db_connection)):
    """Return role-specific KRAs that are measurable (SMART-style)."""
    ctx = await _get_role_context(conn, key)
    role = (ctx.get("role") or "Role")
    department = (ctx.get("department") or "Department")
    profession = (ctx.get("profession") or "Discipline")

    # Helpers reused from day_to_day
    def _extract_items_from_text(text: str) -> List[str]:
        t = text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1] if "\n" in t else t
            if t.endswith("```"):
                t = t.rsplit("```", 1)[0]
        try:
            data = json.loads(t)
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return [str(x).strip() for x in data.get("items", [])]
            if isinstance(data, list):
                return [str(x).strip() for x in data]
        except Exception:
            pass
        lines = [ln.strip("- •\t ") for ln in t.splitlines() if ln.strip()]
        return lines

    def _tokens(*parts: str) -> List[str]:
        raw = " ".join([p for p in parts if p])
        toks = set()
        for w in raw.lower().replace("/", " ").replace("&", " ").split():
            if len(w) >= 4:
                toks.add(w)
        exp = set()
        for k in list(toks):
            if "claim" in k: exp.update(["claim", "adjudicat", "settlement"]) 
            if "fraud" in k: exp.update(["fraud", "investigat", "anti-fraud"]) 
            if "underwrit" in k: exp.update(["underwrit", "risk", "policy"]) 
            if "sales" in k or "business" in k: exp.update(["sales", "pipeline", "revenue", "crm"]) 
        toks.update(exp)
        return list(toks)

    def _is_specific(s: str) -> bool:
        s_low = s.lower()
        has_metric = any(x in s_low for x in ["%", ">=", "<=", "< ", "> ", " within ", " by ", "tat", "sla", "hours", "quarter", "month", "week"])
        has_number = any(ch.isdigit() for ch in s)
        return has_metric or has_number

    def _on_topic(s: str, toks: List[str]) -> bool:
        s_low = s.lower()
        return any(t in s_low for t in toks)

    def _postprocess(items: List[str], toks: List[str], limit: int, fallback: List[str]) -> List[str]:
        cleaned = []
        for it in items:
            it = str(it).strip().strip('"')
            if not it:
                continue
            if _on_topic(it, toks) and _is_specific(it):
                cleaned.append(it)
        if len(cleaned) < limit:
            need = limit - len(cleaned)
            for it in fallback:
                if it not in cleaned:
                    cleaned.append(it)
                if len(cleaned) >= limit:
                    break
        return cleaned[:limit]

    def deterministic_kras() -> list[str]:
        r = role.lower(); d = department.lower()
        base = [
            f"Achieve ≥ 95% SLA adherence for key {r} processes by Q4",
            f"Reduce defect/rework rate in {r} outputs to < 2% by end of quarter",
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

    topic_tokens = _tokens(profession, department, role)

    if API_KEY:
        try:
            prompt = (
                "Generate SMART KRAs for the role below. Each KRA must include a measurable target (%, count, or time), timeframe, and scope.\n"
                f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                "Return STRICT JSON with key 'items' as an array of 6-8 strings. Items must be ON-TOPIC to the role and measurable (SMART)."
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = await asyncio.to_thread(model.generate_content, prompt)
            text = resp.text if hasattr(resp, "text") else str(resp)
            items_raw = _extract_items_from_text(text)
            processed = _postprocess(items_raw, topic_tokens, 8, deterministic_kras())
            return {"items": processed}
        except Exception as e:
            logging.warning("Gemini kras failed, using deterministic: %s", e)
            return {"items": deterministic_kras()}
    else:
        return {"items": deterministic_kras()}