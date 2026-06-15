"""JSON API для фронтенда Pulse.

Подключается к существующему сервисному слою Site Monitor — никакой дублирующей
логики БД. Отдаёт JSON в том виде, который ожидает фронтенд (app/static/pulse.html).

Подключён в app/main.py: app.include_router(api_router).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Check, Site
from app.services import sites as sites_service
from app.services.monitor import check_single

router = APIRouter(prefix="/api", tags=["api"])


def _iso_utc(dt: datetime | None) -> str | None:
    """Бэкенд хранит наивный UTC — отдаём фронту явный ISO с таймзоной."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class CheckOut(BaseModel):
    id: int
    checked_at: datetime
    is_up: bool
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str | None = None

    model_config = {"from_attributes": True}

    @field_serializer("checked_at")
    def _ser_checked_at(self, v: datetime) -> str | None:
        return _iso_utc(v)


class SiteOut(BaseModel):
    id: int
    name: str
    url: str
    interval_minutes: int
    expected_status: int | None = None
    current_status: str | None = None
    last_checked_at: datetime | None = None
    created_at: datetime | None = None
    checks: list[CheckOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @field_serializer("last_checked_at", "created_at")
    def _ser_dt(self, v: datetime | None) -> str | None:
        return _iso_utc(v)


class SiteIn(BaseModel):
    name: str = ""
    url: str
    interval_minutes: int = 5
    expected_status: int | None = 200


def _site_out(site: Site, checks: list[Check]) -> SiteOut:
    # recent_checks отдаёт от новых к старым; фронт ждёт хронологически (старые → новые)
    ordered = list(reversed(checks))
    return SiteOut(
        id=site.id,
        name=site.name,
        url=site.url,
        interval_minutes=site.interval_minutes,
        expected_status=site.expected_status,
        current_status=site.current_status,
        last_checked_at=site.last_checked_at,
        created_at=site.created_at,
        checks=[CheckOut.model_validate(c) for c in ordered],
    )


@router.get("/sites", response_model=list[SiteOut])
async def api_list_sites(session: AsyncSession = Depends(get_session)):
    sites = await sites_service.list_sites(session)
    out: list[SiteOut] = []
    for s in sites:
        # 48 проверок — достаточно для sparkline и uptime за 24ч
        checks = await sites_service.recent_checks(session, s.id, limit=48)
        out.append(_site_out(s, checks))
    return out


@router.get("/sites/{site_id}", response_model=SiteOut)
async def api_get_site(site_id: int, session: AsyncSession = Depends(get_session)):
    site = await sites_service.get_site(session, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    checks = await sites_service.recent_checks(session, site_id, limit=200)
    return _site_out(site, checks)


@router.post("/sites", response_model=SiteOut, status_code=201)
async def api_create_site(payload: SiteIn, session: AsyncSession = Depends(get_session)):
    try:
        site = await sites_service.create_site(
            session,
            name=payload.name,
            url=payload.url,
            interval_minutes=payload.interval_minutes,
            expected_status=payload.expected_status,
        )
    except sites_service.SiteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _site_out(site, [])


@router.post("/sites/{site_id}/check-now", response_model=CheckOut)
async def api_check_now(site_id: int, session: AsyncSession = Depends(get_session)):
    site = await sites_service.get_site(session, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    check = await check_single(session, site)
    await session.commit()
    return CheckOut.model_validate(check)


@router.delete("/sites/{site_id}", status_code=204)
async def api_delete_site(site_id: int, session: AsyncSession = Depends(get_session)):
    site = await sites_service.get_site(session, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await sites_service.delete_site(session, site)
    return None
