import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db import ReviewReport
from app.models.schemas import ReportResponse
from app.services.report import generate_report, PeriodType

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{period_type}/{period_key}", response_model=ReportResponse)
async def create_report(
    period_type: PeriodType,
    period_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """生成指定周期的知识体系报告"""
    settings = get_settings()
    
    try:
        report_result, time_start, time_end, entries = await generate_report(
            db=db,
            period_type=period_type,
            period_key=period_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
    
    # 检查是否已存在相同周期的报告
    stmt = select(ReviewReport).where(
        ReviewReport.period_type == period_type,
        ReviewReport.period_key == period_key,
        ReviewReport.user_id == "local",
    )
    result = await db.execute(stmt)
    existing_report = result.scalar_one_or_none()
    
    if existing_report:
        # 更新现有报告
        existing_report.report_json = report_result.model_dump_json(by_alias=True)
        existing_report.report_version = settings.report_version
        from datetime import datetime
        existing_report.generated_at = datetime.utcnow()
        report = existing_report
    else:
        # 创建新报告
        report = ReviewReport(
            period_type=period_type,
            period_key=period_key,
            time_start=time_start,
            time_end=time_end,
            report_json=report_result.model_dump_json(by_alias=True),
            report_version=settings.report_version,
        )
        db.add(report)
    
    await db.commit()
    await db.refresh(report)
    
    return ReportResponse(
        id=report.id,
        period_type=report.period_type,
        period_key=report.period_key,
        time_start=report.time_start,
        time_end=report.time_end,
        report_json=json.loads(report.report_json) if report.report_json else None,
        generated_at=report.generated_at,
    )


@router.get("/{period_type}/{period_key}", response_model=ReportResponse)
async def get_report(
    period_type: PeriodType,
    period_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取指定周期的报告（如果存在）"""
    stmt = select(ReviewReport).where(
        ReviewReport.period_type == period_type,
        ReviewReport.period_key == period_key,
        ReviewReport.user_id == "local",
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        id=report.id,
        period_type=report.period_type,
        period_key=report.period_key,
        time_start=report.time_start,
        time_end=report.time_end,
        report_json=json.loads(report.report_json) if report.report_json else None,
        generated_at=report.generated_at,
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    period_type: PeriodType | None = None,
    limit: int = 20,
):
    """列出所有报告"""
    stmt = select(ReviewReport).where(ReviewReport.user_id == "local")
    if period_type:
        stmt = stmt.where(ReviewReport.period_type == period_type)
    stmt = stmt.order_by(ReviewReport.generated_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    reports = result.scalars().all()
    
    return [
        ReportResponse(
            id=r.id,
            period_type=r.period_type,
            period_key=r.period_key,
            time_start=r.time_start,
            time_end=r.time_end,
            report_json=json.loads(r.report_json) if r.report_json else None,
            generated_at=r.generated_at,
        )
        for r in reports
    ]
