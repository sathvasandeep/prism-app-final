# routes/ai_async.py
import os
import json
import re
import asyncio
from typing import Dict, List, Optional

import aiomysql
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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
async def get_conn():
    conn = await aiomysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        autocommit=True,
    )
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass

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
        prompt = (
            "Generate 8-10 SMART day-to-day activities as JSON {\"items\": [\"...\"]}.\n"
            f"Profession: {profession}\nDepartment: {department}\nRole: {role}\n"
            "Be specific, measurable, relevant to the role context."
        )
        for attempt in range(2):
            try:
                resp = await _model.generate_content_async(prompt)
                text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "")
                items_raw = _extract_items_json(text)
                items = []
                for it in items_raw:
                    s = it.strip()
                    if s and all(t not in s.lower() for t in toks):
                        items.append(s)
                if len(items) < 6:
                    items = deterministic_items()
                return {"items": items, "source": "ai"}
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                return {"items": deterministic_items(), "source": "default"}
    return {"items": deterministic_items(), "source": "default"}

@router.post("/kras")
async def suggest_kras(key: RoleKey, conn = Depends(get_conn)):
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

    if _model and not DISABLE_AI:
        prompt = (
            "Generate 6-8 SMART KRAs as JSON {\"items\": [\"...\"]}.\n"
            f"Profession: {profession}\nDepartment: {department}\nRole: {role}"
        )
        for attempt in range(2):
            try:
                resp = await _model.generate_content_async(prompt)
                text = resp.text if hasattr(resp, "text") else (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "")
                items_raw = _extract_items_json(text)
                items = []
                for it in items_raw:
                    s = it.strip()
                    if s and all(t not in s.lower() for t in toks):
                        items.append(s)
                if len(items) < 5:
                    items = deterministic_kras()
                return {"items": items, "source": "ai"}
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                return {"items": deterministic_kras(), "source": "default"}
    return {"items": deterministic_kras(), "source": "default"}

@router.post("/objectives")
async def suggest_objectives(req: ObjectiveRequest, conn = Depends(get_conn)) -> ObjectiveResponse:
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

    if _model and not DISABLE_AI:
        prompt = (
            "You are an assistant generating SMART simulation objectives for a specific SKIVE sub-competency.\n\n"
            f"Profession: {profession}\nDepartment: {department}\nRole: {role}\nPath: {path}\n\n"
            "Respond ONLY with JSON object: {\"basic\": \"...\", \"intermediate\": \"...\", \"advanced\": \"...\"}."
        )
        for attempt in range(2):
            try:
                resp = await _model.generate_content_async(prompt)
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
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.3)
                    continue
                det = _deterministic_objectives(path)
                return ObjectiveResponse(levels=det, source="default")
    det = _deterministic_objectives(path)
    return ObjectiveResponse(levels=det, source="default")
