# routes/ai_async.py
import os
import json
import re
import asyncio
from typing import Dict, List, Optional

import aiomysql
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Optional Gemini config
try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None

API_KEY = os.getenv("GEMINI_API_KEY")
DISABLE_AI = os.getenv("DISABLE_AI", "1") == "1"
if API_KEY and genai is not None:
    try:
        genai.configure(api_key=API_KEY)
        _model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:  # pragma: no cover
        _model = None
else:
    _model = None

router = APIRouter()

# --- Models ---
class RoleKey(BaseModel):
    profession: Optional[int] = None
    department: Optional[int] = None
    role: Optional[int] = None

class ObjectiveLevels(BaseModel):
    basic: str
    intermediate: str
    advanced: str

class ObjectiveRequest(BaseModel):
    key: RoleKey
    path: str  # e.g. "skills.cognitive.analytical"

class ObjectiveResponse(BaseModel):
    levels: ObjectiveLevels
    source: str

# --- DB ---
from fastapi import Request

async def get_conn(request: Request):
    pool = request.app.state.mysql_pool
    async with pool.acquire() as conn:
        yield conn

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

# --- Helpers ---
def _tokens(*parts: str) -> List[str]:
    return [p.lower() for p in parts if p]

def _extract_items_json(text: str) -> List[str]:
    try:
        if not text:
            return []
        s = text.strip()
        if s.startswith("```"):
            s = "\n".join(s.splitlines()[1:])
            if s.strip().endswith("```"):
                s = "\n".join(s.splitlines()[:-1])
            s = s.strip()
        try:
            data = json.loads(s)
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return [str(x) for x in data.get("items", [])]
        except Exception:
            pass
        m = re.search(r"\{\s*\"items\"\s*:\s*(\[.*?\])\s*\}", s, re.DOTALL)
        if m:
            arr = json.loads(m.group(1))
            if isinstance(arr, list):
                return [str(x) for x in arr]
    except Exception:
        return []
    return []

# --- AI endpoints ---
@router.post("/day_to_day")
async def suggest_day_to_day(key: RoleKey, conn = Depends(get_conn)):
    ctx = await _resolve_role_context(conn, key)
    profession = ctx.get("profession", ""); department = ctx.get("department", ""); role = ctx.get("role", "")
    toks = _tokens(profession, department, role)

    def deterministic_items() -> List[str]:
        r = role.lower(); d = department.lower()
        base = [
            f"Review {r} queue and triage high-priority items by 10 AM",
            f"Prepare and analyze {r} metrics dashboard; share insights weekly",
            f"Collaborate with {d} stakeholders to unblock dependencies",
            f"Perform peer QA on team outputs and log defects",
            f"Document key decisions and updates in the wiki",
            f"Attend stand-up and align on next actions",
            f"Respond to pending queries within SLA",
            f"Identify one improvement and add to backlog",
            f"Update project board with status and blockers",
            f"Share daily summary with next steps by EOD",
        ]
        return [b for b in base if b]

    if _model and not DISABLE_AI:
        logging.info("Gemini AI called for day_to_day.")
        prompt = (
            "Generate 8-10 SMART day-to-day activities as JSON {\"items\": [\"...\"]}.\n"
            f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
            "Be specific, measurable, relevant to the role context."
        )
        for attempt in range(2):
            try:
                prompt = (
                    "Generate 8-10 SMART day-to-day activities as JSON {\"items\": [\"...\"]}.\n"
                    f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
                    "Be specific, measurable, relevant to the role context."
                )
                resp = await _model.generate_content_async(prompt)
                logging.info("[day_to_day] Gemini AI success.")
                text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "")
                items_raw = _extract_items_json(text)
                items = []
                for it in items_raw:
                    s = it.strip()
                    if s and all(t not in s.lower() for t in toks):
                        items.append(s)
                if len(items) < 6:
                    logging.info("[day_to_day] Gemini AI fallback triggered due to insufficient items.")
                    items = deterministic_items()
                return {"items": items, "source": "ai"}
            except Exception as e:
                logging.error(f"[day_to_day] Gemini failed: {e}", exc_info=True)
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                logging.info("[day_to_day] Gemini AI fallback triggered after error.")
                return {"items": deterministic_items(), "source": "default"}
        else:
            logging.info("[day_to_day] Gemini AI not called: using fallback.")
            return {"items": deterministic_items(), "source": "default"}
    logging.info("Gemini AI fallback triggered for day_to_day.")
    return {"items": deterministic_items(), "source": "default"}

@router.post("/kras")
async def suggest_kras(key: RoleKey, request: Request, conn = Depends(get_conn)):
    _model = request.app.state.gemini_model
    DISABLE_AI = request.app.state.disable_ai
    logging.info(f"[kras] ENTRY: _model={_model}, DISABLE_AI={DISABLE_AI}")
    ctx = await _resolve_role_context(conn, key)
    profession = ctx.get("profession", ""); department = ctx.get("department", ""); role = ctx.get("role", "")
    toks = _tokens(profession, department, role)

    def deterministic_kras() -> List[str]:
        r = role.lower()
        return [
            f"Achieve ≥ 95% SLA adherence for key {r} processes by Q4",
            f"Reduce defect rate in {r} outputs to < 2% by end of quarter",
            f"Improve cross-team collaboration with 2 initiatives this quarter",
            f"Increase automation coverage by 15% for {r} workflows",
            f"Publish monthly KPI review with corrective actions",
            f"Deliver two process improvements saving ≥ 5% effort",
            f"Maintain stakeholder NPS ≥ 8.5/10 across counterparts",
            f"Identify and mitigate top 3 operational risks quarterly",
        ]

    for attempt in range(2):
        if _model and not DISABLE_AI:
            logging.info("[kras] Gemini AI will be called.")
            try:
                prompt = (
                    "Generate 6-8 SMART KRAs as JSON {\"items\": [\"...\"]}.\n"
                    f"Profession: {profession}\nDepartment: {department}\nRole: {role}"
                )
                resp = await _model.generate_content_async(prompt)
                logging.info("[kras] Gemini AI success.")
                text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "")
                items_raw = _extract_items_json(text)
                items = []
                for it in items_raw:
                    s = it.strip()
                    if s and all(t not in s.lower() for t in toks):
                        items.append(s)
                if len(items) < 5:
                    logging.info("[kras] Gemini AI fallback triggered due to insufficient items.")
                    items = deterministic_kras()
                return {"items": items, "source": "ai"}
            except Exception as e:
                logging.error(f"[kras] Gemini failed: {e}", exc_info=True)
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                logging.info("[kras] Gemini AI fallback triggered after error.")
                return {"items": deterministic_kras(), "source": "default"}
        else:
            logging.info("[kras] Gemini AI not called: using fallback.")
            return {"items": deterministic_kras(), "source": "default"}
    logging.info("Gemini AI fallback triggered for kras.")
    return {"items": deterministic_kras(), "source": "default"}

@router.post("/objectives")
async def suggest_objectives(req: ObjectiveRequest, request: Request, conn = Depends(get_conn)) -> ObjectiveResponse:
    _model = request.app.state.gemini_model
    DISABLE_AI = request.app.state.disable_ai
    logging.info(f"[objectives] ENTRY: _model={_model}, DISABLE_AI={DISABLE_AI}")
    path = req.path
    ctx = await _resolve_role_context(conn, req.key)
    profession = ctx.get("profession", "").strip() or ""
    department = ctx.get("department", "").strip() or ""
    role = ctx.get("role", "").strip() or ""

    def _deterministic_objectives(p: str) -> ObjectiveLevels:
        base = p.split(".")[-1].replace("_", " ")
        return ObjectiveLevels(
            basic=f"Demonstrate basic competence in {base} by completing 2 guided tasks within 2 weeks.",
            intermediate=f"Independently apply {base} to solve 3 realistic cases with <10% errors within a month.",
            advanced=f"Lead a complex scenario requiring {base}, documenting approach and outcomes within this quarter."
        )

    for attempt in range(2):
        if _model and not DISABLE_AI:
            logging.info("[objectives] Gemini AI will be called.")
            try:
                prompt = (
                    "You are an assistant generating SMART simulation objectives for a specific SKIVE sub-competency.\n\n"
                    f"Profession: {profession}\nDepartment: {department}\nRole: {role}\nPath: {path}\n\n"
                    "Respond ONLY with JSON object: {\"basic\": \"...\", \"intermediate\": \"...\", \"advanced\": \"...\"}."
                )
                resp = await _model.generate_content_async(prompt)
                logging.info("[objectives] Gemini AI success.")
                text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "")
                s = text.strip() if text else ""
                if s.startswith("```"):
                    s = "\n".join(s.splitlines()[1:])
                    if s.strip().endswith("```"):
                        s = "\n".join(s.splitlines()[:-1])
                    s = s.strip()
                data = json.loads(s)
                if not isinstance(data, dict):
                    raise ValueError("Parse failure")
                levels = ObjectiveLevels(
                    basic=str(data.get("basic", "")).strip() or _deterministic_objectives(path).basic,
                    intermediate=str(data.get("intermediate", "")).strip() or _deterministic_objectives(path).intermediate,
                    advanced=str(data.get("advanced", "")).strip() or _deterministic_objectives(path).advanced,
                )
                return ObjectiveResponse(levels=levels, source="ai")
            except Exception as e:
                logging.error(f"[objectives] Gemini failed: {e}", exc_info=True)
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                logging.info("[objectives] Gemini AI fallback triggered after error.")
                det = _deterministic_objectives(path)
                return ObjectiveResponse(levels=det, source="default")
        else:
            logging.info("[objectives] Gemini AI not called: using fallback.")
            det = _deterministic_objectives(path)
            return ObjectiveResponse(levels=det, source="default")
    logging.info("Gemini AI fallback triggered for objectives.")
    det = _deterministic_objectives(path)
    return ObjectiveResponse(levels=det, source="default")
class ArchetypeInfoRequest(BaseModel):
    profession: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    global_archetype_profile: Optional[str] = None

class ArchetypeInfoResponse(BaseModel):
    archetype: dict
    global_archetype_summary: str
    profession_info: dict
    source: str

@router.post("/archetype_info", response_model=ArchetypeInfoResponse)
async def suggest_archetype_info(
    req: ArchetypeInfoRequest,
    request: Request,
    conn = Depends(get_conn)
) -> ArchetypeInfoResponse:
    import traceback
    # --- Resolve profession, department, role IDs to names ---
    from .ai_async import _resolve_role_context
    ctx = await _resolve_role_context(conn, req)
    profession = ctx.get("profession", "")
    department = ctx.get("department", "")
    role = ctx.get("role", "")
    try:
        _model = request.app.state.gemini_model
        DISABLE_AI = request.app.state.disable_ai
        # --- main logic continues here ---
    except Exception:
        return ArchetypeInfoResponse(
            archetype={
                "name": "Analytical Strategist",
                "description": "Data-driven decision maker, excels at breaking down complex problems, and devising actionable strategies.",
                "examples": ["Management Consultant"]
            },
            global_archetype_summary="This role operates at a strategic level, requiring high-level decision making, critical evaluation, and empathy. Supporting skills include precision, coordination, self-regulation, and mastery of both technical and interpersonal competencies.",
            profession_info={
                "summary": f"The {profession} in {department} ({role}) plays a key role in organizational success.",
                "years_to_role": "5-8 years",
                "qualifications": "Master's in Data Science or related field",
                "certifications": "Certified Data Scientist (CDS), AWS Certified Machine Learning",
                "salary_range": "$120,000 - $180,000 USD",
                "perks": "Flexible hours, remote work, conference travel, stock options",
                "highs": "High impact, leadership, innovation opportunities",
                "lows": "High pressure, rapid tech changes, cross-team dependencies",
                "career_pathway": "Senior Data Scientist → Lead Data Scientist → Manager of Data Science → Director of Analytics"
            },
            source="default"
        )

    # --- New AI logic ---
    import importlib.util
    import ast
    import sys
    logic_path = "backend/archetype_logic.py"
    spec = importlib.util.spec_from_file_location("archetype_logic", logic_path)
    archetype_logic = importlib.util.module_from_spec(spec)
    sys.modules["archetype_logic"] = archetype_logic
    spec.loader.exec_module(archetype_logic)

    def parse_skive(skive_str):
        # Try to safely parse the incoming string as a dict
        try:
            return ast.literal_eval(skive_str)
        except Exception:
            return {}

    global_profile = getattr(req, "global_archetype_profile", "") or ""
    skive = parse_skive(global_profile)
    flat = archetype_logic.flatten_skive(skive) if skive else []
    high_comp = [k for k, v in flat if archetype_logic.get_tier(v) == "High"]
    medium_comp = [k for k, v in flat if archetype_logic.get_tier(v) == "Medium"]
    high_comp_str = ", ".join(high_comp) if high_comp else "None"
    medium_comp_str = ", ".join(medium_comp) if medium_comp else "None"

    import traceback
    logging.info(f"[archetype_info] ENTRY: profession={profession}, department={department}, role={role}, global_profile={str(global_profile)[:100]}")
    for attempt in range(2):
        if _model and not DISABLE_AI:
            try:
                # Prompt 1: Global Archetype Summary
                dna_prompt = f"""
You are an expert Organizational Behavior consultant and a master of pedagogical design, specializing in analyzing professional roles. I will provide you with a \"Role DNA\" profile, which is a list of competencies required for a specific job, rated on their importance (High or Medium).
Your task is to synthesize this raw data into a concise, insightful Global Archetype Summary.
Instructions:
Identify the Core Theme: First, analyze the list of 'High' rated competencies. Identify the dominant theme. Is this role primarily analytical, interpersonal, ethical, or something else?
Craft an Archetype Title: Based on the core theme, create a compelling archetype title that captures the essence of the role (e.g., \"The Ethical Innovator,\" \"The Data-Driven Strategist,\" \"The Empathetic Collaborator\").
Write the Summary Narrative (2-3 paragraphs):
> * Start by stating the core theme and the archetype you've identified.
> * Explain why this theme is dominant, referencing the 2-3 most important 'High' rated skills.
> * Describe how the other 'High' rated skills support this core theme.
> * Address any apparent contradictions or interesting combinations (e.g., \"This profile is unique because it combines high technical proficiency with a strong demand for empathy...\").
> * Reference the 'Medium' rated skills as the \"professional baseline\" or \"expected foundation\" for this role.
> * If any of the 5 main SKIVE dimensions (Skills, Knowledge, Identity, Values, Ethics) have a noticeably lower average score, comment on what this implies about the role's focus (e.g., \"While Skills and Knowledge scores are lower, this doesn't indicate a lack of capability, but rather that the primary focus of this role lies in the value-driven aspects of the work...\").
Tone: Your tone should be insightful, professional, and affirmative. You are describing the demands of the role, not judging a person.
High Importance Competencies:
{high_comp_str}
Medium Importance Competencies:
{medium_comp_str}
Respond with a JSON object: {{ "archetype": {{ "name": str, "description": str, "examples": [str, ...] }}, "global_archetype_summary": str }}
"""
                resp1 = await _model.generate_content_async(dna_prompt)
                text1 = resp1.text if hasattr(resp1, "text") else (resp1.candidates[0].content.parts[0].text if resp1 and resp1.candidates else "")
                s1 = text1.strip() if text1 else ""
                if s1.startswith("```"):
                    s1 = "\n".join(s1.splitlines()[1:])
                    if s1.strip().endswith("```"):
                        s1 = "\n".join(s1.splitlines()[:-1])
                    s1 = s1.strip()
                data1 = json.loads(s1)
                # Prompt 2: Profession Info
                prof_prompt = f"""
You are an expert career research analyst with access to vast amounts of public domain data about professional roles. I will provide you with a specific job title, including its profession and department.
Your task is to generate a concise, realistic, and helpful \"Profession Info\" summary for this role.
Instructions:
Research the provided role based on publicly available information (from sources like LinkedIn, Glassdoor, industry reports, job postings, etc.).
Provide a summary for each of the following categories.
If specific data (like salary) is hard to find for the exact role, provide a reasonable estimate for a similar role in a major market (e.g., USA, Europe) and state that it is an estimate.
If a category is truly unknowable or highly variable (like \"Perks\"), describe the types of things one might expect.
The tone should be informative, realistic, and helpful to someone considering this career path.
Never respond with 'Unable to determine.' If information is missing, use your best judgment to provide a plausible, helpful answer.
Profession: {profession}
Department: {department}
Specific Role: {role}
Respond with a JSON object: {{ "profession_info": {{ "summary": str, "years_to_role": str, "qualifications": str, "certifications": str, "salary_range": str, "perks": str, "highs": str, "lows": str, "career_pathway": str }} }}
"""
                resp2 = await _model.generate_content_async(prof_prompt)
                text2 = resp2.text if hasattr(resp2, "text") else (resp2.candidates[0].content.parts[0].text if resp2 and resp2.candidates else "")
                s2 = text2.strip() if text2 else ""
                if s2.startswith("```"):
                    s2 = "\n".join(s2.splitlines()[1:])
                    if s2.strip().endswith("```"):
                        s2 = "\n".join(s2.splitlines()[:-1])
                    s2 = s2.strip()
                data2 = json.loads(s2)
                if not ("archetype" in data1 and "global_archetype_summary" in data1 and "profession_info" in data2):
                    raise ValueError("Parse failure")
                return ArchetypeInfoResponse(
                    archetype=data1["archetype"],
                    global_archetype_summary=data1["global_archetype_summary"],
                    profession_info=data2["profession_info"],
                    source="ai"
                )
            except Exception as e:
                tb = traceback.format_exc()
                logging.error(f"[archetype_info] Gemini failed: {e}\n{tb}")
                # Return error details in response for debugging (remove in prod)
                return ArchetypeInfoResponse(
                    archetype={},
                    global_archetype_summary="",
                    profession_info={"error": str(e), "traceback": tb},
                    source="error"
                )
        else:
            return fallback()
    return fallback()