import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db import DailyEntry
from app.models.schemas import EntryCreate, EntryResponse, EnrichmentResult
from app.services.enrichment import enrich_entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=EntryResponse)
async def create_entry(
    data: EntryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """提交一条学习记录，自动结构化"""
    settings = get_settings()
    
    # 创建条目
    entry = DailyEntry(
        entry_text=data.entry_text,
        enrich_version=settings.enrich_version,
    )
    
    # 调用 LLM 进行结构化
    try:
        enrich_result = await enrich_entry(data.entry_text)
        entry.enrich_json = enrich_result.model_dump_json(by_alias=True)
    except Exception as e:
        # LLM 调用失败时仍然保存条目，但不包含 enrich_json
        entry.enrich_json = None
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    # 构建响应
    response = EntryResponse(
        id=entry.id,
        created_at=entry.created_at,
        entry_text=entry.entry_text,
        enrich_json=json.loads(entry.enrich_json) if entry.enrich_json else None,
    )
    return response


@router.get("", response_model=list[EntryResponse])
async def list_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
):
    """获取学习记录列表"""
    stmt = (
        select(DailyEntry)
        .where(DailyEntry.user_id == "local")
        .order_by(DailyEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    responses = []
    for entry in entries:
        responses.append(EntryResponse(
            id=entry.id,
            created_at=entry.created_at,
            entry_text=entry.entry_text,
            enrich_json=json.loads(entry.enrich_json) if entry.enrich_json else None,
        ))
    return responses


@router.get("/{entry_id}", response_model=EntryResponse)
async def get_entry(
    entry_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取单条学习记录"""
    stmt = select(DailyEntry).where(DailyEntry.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return EntryResponse(
        id=entry.id,
        created_at=entry.created_at,
        entry_text=entry.entry_text,
        enrich_json=json.loads(entry.enrich_json) if entry.enrich_json else None,
    )
