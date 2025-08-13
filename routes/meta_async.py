# routes/meta_async.py
import os
from typing import Optional
import aiomysql
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

from fastapi import Request

async def get_conn(request: Request):
    pool = request.app.state.mysql_pool
    async with pool.acquire() as conn:
        yield conn

@router.get("/professions")
async def get_professions(conn = Depends(get_conn)):
    try:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute("SELECT id, name FROM professions ORDER BY id LIMIT 20")
        rows = await cursor.fetchall()
        await cursor.close()
        return rows
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch professions")

@router.get("/departments")
async def get_departments(profession_id: Optional[str] = None, conn = Depends(get_conn)):
    try:
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
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

@router.get("/roles")
async def get_roles(department_id: Optional[str] = None, conn = Depends(get_conn)):
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
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch roles")
