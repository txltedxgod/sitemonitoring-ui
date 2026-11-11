"""Integration and unit tests for Pulse JSON API, Starlette templates, and HTML escaping."""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import database, main, scheduler
from app.models import Base, Site
from app.services import checker, monitor, telegram
from app.services.checker import CheckResult


@pytest.fixture()
def pulse_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    db_file = tmp_path / "pulse_test.db"
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file.as_posix()}", echo=False, future=True
    )
    test_session_maker = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )

    monkeypatch.setattr(main.settings, "database_url", f"sqlite+aiosqlite:///{db_file.as_posix()}")
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "async_session", test_session_maker)
    monkeypatch.setattr(scheduler, "start_scheduler", lambda: None)
    monkeypatch.setattr(scheduler, "shutdown_scheduler", lambda: None)
    monkeypatch.setattr(main, "start_scheduler", lambda: None)
    monkeypatch.setattr(main, "shutdown_scheduler", lambda: None)

    async def test_init_db() -> None:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(main, "init_db", test_init_db)

    async def fake_check(*args, **kwargs) -> CheckResult:
        return CheckResult(True, 200, 18.4, None)

    async def fake_send(*args, **kwargs) -> bool:
        return True

    monkeypatch.setattr(checker, "check_site", fake_check)
    monkeypatch.setattr(telegram, "send_message", fake_send)

    app = main.create_app()
    with TestClient(app) as client:
        yield client


def test_health_dashboard_and_pulse_spa(pulse_client: TestClient) -> None:
    assert pulse_client.get("/health").json()["status"] == "healthy"
    assert pulse_client.get("/").status_code == 200
    ui = pulse_client.get("/ui")
    assert ui.status_code == 200
    assert "text/html" in ui.headers["content-type"]


def test_pulse_json_api_crud_and_check_now(pulse_client: TestClient) -> None:
    bad = pulse_client.post(
        "/api/sites",
        json={"name": "Bad", "url": "ftp://invalid.local", "interval_minutes": 5},
    )
    assert bad.status_code == 400

    created = pulse_client.post(
        "/api/sites",
        json={"name": "API Edge", "url": "https://api.example.com", "interval_minutes": 5},
    )
    assert created.status_code == 201
    site_id = created.json()["id"]

    checked = pulse_client.post(f"/api/sites/{site_id}/check-now")
    assert checked.status_code == 200
    assert checked.json()["is_up"] is True
    assert checked.json()["checked_at"].endswith("+00:00")

    detail_html = pulse_client.get(f"/sites/{site_id}")
    assert detail_html.status_code == 200
    assert "API Edge" in detail_html.text

    listed = pulse_client.get("/api/sites")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = pulse_client.delete(f"/api/sites/{site_id}")
    assert deleted.status_code == 204
    assert pulse_client.get(f"/api/sites/{site_id}").status_code == 404


def test_alert_html_escaping() -> None:
    site = Site(
        name="Prod <Edge> & DB", url="https://example.com?a=1&b=2", interval_minutes=5
    )
    msg = monitor._format_alert(
        site, CheckResult(False, 502, 5.0, "Bad <Gateway>"), recovered=False
    )
    assert "Prod &lt;Edge&gt; &amp; DB" in msg
    assert "Bad &lt;Gateway&gt;" in msg
