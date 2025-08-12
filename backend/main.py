from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from archetype_logic import generate_archetype_narrative

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArchetypeRequest(BaseModel):
    profile_id: int
    profession: int
    department: int
    role: int
    skive: Dict[str, Dict[str, int]]

@app.post("/api/archetype")
def archetype_endpoint(payload: ArchetypeRequest):
    # Use only skive for now; expand as needed
    result = generate_archetype_narrative(payload.skive)
    return {"archetype": result}
