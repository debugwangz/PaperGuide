import json
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import DailyEntry
from app.models.schemas import ReportResult, EnrichmentResult
from app.prompts.templates import REPORT_SYSTEM_PROMPT, REPORT_USER_PROMPT
from app.services.llm import get_llm_provider

PeriodType = Literal["week", "month", "quarter", "year"]


def parse_period_key(period_type: PeriodType, period_key: str) -> tuple[datetime, datetime]:
    """解析周期标识，返回 (time_start, time_end)"""
    if period_type == "week":
        # 格式: 2026-W06
        year, week = period_key.split("-W")
        year, week = int(year), int(week)
        # ISO week: Monday is day 1
        from datetime import timedelta
        jan4 = datetime(year, 1, 4)
        start_of_week1 = jan4 - timedelta(days=jan4.isoweekday() - 1)
        time_start = start_of_week1 + timedelta(weeks=week - 1)
        time_end = time_start + timedelta(days=7) - timedelta(seconds=1)
    elif period_type == "month":
        # 格式: 2026-02
        year, month = period_key.split("-")
        year, month = int(year), int(month)
        time_start = datetime(year, month, 1)
        if month == 12:
            time_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            time_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    elif period_type == "quarter":
        # 格式: 2026-Q1
        year, q = period_key.split("-Q")
        year, q = int(year), int(q)
        start_month = (q - 1) * 3 + 1
        time_start = datetime(year, start_month, 1)
        end_month = start_month + 3
        if end_month > 12:
            time_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            time_end = datetime(year, end_month, 1) - timedelta(seconds=1)
    elif period_type == "year":
        # 格式: 2026
        year = int(period_key)
        time_start = datetime(year, 1, 1)
        time_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        raise ValueError(f"Invalid period_type: {period_type}")
    
    return time_start, time_end


async def get_entries_in_period(
    db: AsyncSession, 
    time_start: datetime, 
    time_end: datetime,
    user_id: str = "local"
) -> list[DailyEntry]:
    """获取指定时间范围内的所有条目"""
    stmt = (
        select(DailyEntry)
        .where(DailyEntry.user_id == user_id)
        .where(DailyEntry.created_at >= time_start)
        .where(DailyEntry.created_at <= time_end)
        .order_by(DailyEntry.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def prepare_entries_for_prompt(entries: list[DailyEntry]) -> str:
    """将条目列表转换为 LLM prompt 使用的 JSON 字符串"""
    entries_data = []
    for entry in entries:
        entry_dict = {
            "id": entry.id,
            "created_at": entry.created_at.isoformat(),
        }
        if entry.enrich_json:
            enrich_data = json.loads(entry.enrich_json)
            entry_dict.update({
                "summary": enrich_data.get("summary", ""),
                "entities": enrich_data.get("entities", []),
                "claims": enrich_data.get("claims", []),
                "relations": enrich_data.get("relations", []),
                "prerequisites": enrich_data.get("prerequisites", []),
                "examples": enrich_data.get("examples", []),
                "signals": enrich_data.get("signals", {}),
            })
        entries_data.append(entry_dict)
    return json.dumps(entries_data, ensure_ascii=False, indent=2)


async def generate_report(
    db: AsyncSession,
    period_type: PeriodType,
    period_key: str,
    user_id: str = "local"
) -> tuple[ReportResult, datetime, datetime, list[DailyEntry]]:
    """生成指定周期的知识体系报告"""
    time_start, time_end = parse_period_key(period_type, period_key)
    entries = await get_entries_in_period(db, time_start, time_end, user_id)
    
    if not entries:
        # 没有条目时返回空报告
        from app.models.schemas import OutlineNode, Mainline, Metrics
        empty_report = ReportResult(
            outline_tree=OutlineNode(
                path="本周期知识体系",
                coverage=0,
                node_summary="本周期暂无学习记录",
                evidence_entry_ids=[],
                children=[],
            ),
            mainline=Mainline(
                title="无主线",
                steps=[],
                mainline_score=0.0,
            ),
            gaps=[],
            isolated_items=[],
            metrics=Metrics(
                entry_count=0,
                topic_count=0,
                scatter_score=0.0,
                gap_count=0,
            ),
            repair_plan=[],
        )
        return empty_report, time_start, time_end, entries
    
    llm = get_llm_provider()
    entries_json = prepare_entries_for_prompt(entries)
    user_prompt = REPORT_USER_PROMPT.format(
        period_type=period_type,
        period_key=period_key,
        entries_json=entries_json,
    )
    
    result = await llm.generate_json(
        system_prompt=REPORT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ReportResult,
    )
    return result, time_start, time_end, entries
