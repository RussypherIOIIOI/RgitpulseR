"""Real PostgreSQL contracts. Every test gets an isolated schema, never a shared table reset."""

import asyncio
import importlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest

from test_contract import item

pytestmark = pytest.mark.integration
A = datetime(2026, 1, 28, 12, tzinfo=timezone.utc)
REPO = {"id": 42, "full_name": "example/repo", "private": False}


def store():
    assert importlib.util.find_spec("gitpulse.store"), "PostgreSQL publication is not implemented"
    return importlib.import_module("gitpulse.store")


def golden():
    issues = [
        item(n, created_at=(A - timedelta(days=days)).isoformat(), updated_at=A.isoformat())
        for n, days in enumerate([2, 8, 40, 100], 1)
    ]
    pulls = [
        item(
            n,
            state="closed",
            created_at=(A - timedelta(hours=hours + 1)).isoformat(),
            updated_at=(A - timedelta(hours=1)).isoformat(),
            closed_at=(A - timedelta(hours=1)).isoformat(),
            merged_at=(A - timedelta(hours=1)).isoformat(),
        )
        for n, hours in enumerate([1, 3, 5, 7], 5)
    ]
    return issues, pulls


async def fixture_db(scenario):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database")
    db = await asyncpg.connect(url)
    schema = "test_" + uuid4().hex
    await db.execute(f'CREATE SCHEMA "{schema}"')
    await db.execute(f'SET search_path TO "{schema}"')
    try:
        await db.execute(Path("migrations/001_initial.sql").read_text())
        await scenario(db, url, schema)
    finally:
        # Leave test schemas intact; no destructive cleanup against an owner's database.
        await db.close()


async def publish(db, issues=None, pulls=None, **options):
    if issues is None:
        issues, pulls = golden()

    async def source():
        assert not db.is_in_transaction(), "HTTP fetch must not hold an open transaction"
        return REPO, issues, pulls

    return await store().refresh(
        db, mode="demo", repository="example/repo", source=source, reference=A, **options
    )


async def snapshot(db, *args):
    if not args:
        value = await db.fetchval("SELECT gitpulse_dashboard()")
    else:
        value = await db.fetchval("SELECT gitpulse_dashboard($1,$2,$3,$4,$5)", *args)
    return json.loads(value)


def test_import_twice_is_identical_and_golden_metrics_are_exact():
    async def scenario(db, *_):
        await publish(db)
        before = await db.fetch(
            "SELECT number,source_id,kind,title,author,state,created_at,"
            "updated_at,closed_at,merged_at FROM work_items ORDER BY number"
        )
        first = await snapshot(db)
        await publish(db)
        after = await db.fetch(
            "SELECT number,source_id,kind,title,author,state,created_at,"
            "updated_at,closed_at,merged_at FROM work_items ORDER BY number"
        )
        second = await snapshot(db)
        assert before == after
        assert (
            first["metrics"]
            == second["metrics"]
            == {"medianMergeHours": 4, "medianIssueDays": 24, "openIssues": 4, "mergedPRs": 4}
        )
        assert second["ages"] == [1, 1, 1, 1]
        assert len(second["weeks"]) == 12
        assert sum(w["count"] for w in second["weeks"]) == 4
        assert second["weeks"][-1]["partial"]
        assert await db.fetchval("SELECT count(*) FROM work_items") == 8

    asyncio.run(fixture_db(scenario))


def test_updates_reopens_merges_and_does_not_regress_source_versions():
    async def scenario(db, *_):
        issues = [item()]
        pulls = [item(2)]
        await publish(db, issues, pulls)
        issues = [
            item(
                title="Changed",
                state="closed",
                closed_at="2026-01-04T00:00:00Z",
                updated_at="2026-01-04T00:00:00Z",
            )
        ]
        pulls = [
            item(
                2,
                state="closed",
                closed_at="2026-01-04T00:00:00Z",
                merged_at="2026-01-04T00:00:00Z",
                updated_at="2026-01-04T00:00:00Z",
            )
        ]
        await publish(db, issues, pulls)
        assert (await snapshot(db))["metrics"]["mergedPRs"] == 1
        await publish(db, [item(updated_at="2026-01-05T00:00:00Z", title="Reopened")], pulls)
        await publish(db, [item()], pulls)
        assert await db.fetchval("SELECT title FROM work_items WHERE number=1") == "Reopened"
        assert await db.fetchval("SELECT count(*) FROM work_items") == 2

    asyncio.run(fixture_db(scenario))


def test_failed_write_rolls_back_and_preserves_last_success_then_recovers():
    async def scenario(db, *_):
        await publish(db)
        before = await snapshot(db)
        # Trigger fails on the second insert, after the first item was actually written.
        await db.execute(
            "CREATE FUNCTION fail_write() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN IF NEW.number=2 THEN RAISE EXCEPTION 'injected'; END IF; "
            "RETURN NEW; END $$; CREATE TRIGGER fail_write BEFORE UPDATE ON work_items "
            "FOR EACH ROW EXECUTE FUNCTION fail_write()"
        )
        with pytest.raises(asyncpg.RaiseError):
            await publish(db)
        after = await snapshot(db)
        assert before["dataset"] == after["dataset"]
        assert before["rows"] == after["rows"]
        assert after["latestRun"]["status"] == "failed"
        assert "injected" not in after["latestRun"]["error"]
        await db.execute("ALTER TABLE work_items DISABLE TRIGGER fail_write")
        await publish(db)
        assert (await snapshot(db))["latestRun"]["status"] == "success"

    asyncio.run(fixture_db(scenario))


def test_overlapping_connections_rejected_through_fetch_and_lock_released_on_failure():
    async def scenario(db, url, schema):
        other = await asyncpg.connect(url, server_settings={"search_path": schema})
        entered, release = asyncio.Event(), asyncio.Event()

        async def source():
            entered.set()
            await release.wait()
            raise RuntimeError("secret failure must not be in audit")

        task = asyncio.create_task(
            store().refresh(db, mode="demo", repository="example/repo", source=source, reference=A)
        )
        await entered.wait()
        try:
            with pytest.raises(store().RefreshBusy):
                await publish(other)
        finally:
            release.set()
            with pytest.raises(RuntimeError):
                await task
            await other.close()
        await publish(db)
        assert (await snapshot(db))["latestRun"]["status"] == "success"

    asyncio.run(fixture_db(scenario))


def test_empty_missing_records_and_failed_fetch_keep_publication_coherent():
    async def scenario(db, *_):
        await publish(db)
        await publish(db, [], [])
        value = await snapshot(db)
        assert value["metrics"]["medianMergeHours"] is None
        assert value["metrics"]["medianIssueDays"] is None
        assert value["total"] == 0
        assert len(value["weeks"]) == 12
        assert all(w["count"] == 0 for w in value["weeks"])
        assert await db.fetchval("SELECT count(*) FROM work_items") == 8

        async def broken():
            raise RuntimeError("token=never-log-this")

        with pytest.raises(RuntimeError):
            await store().refresh(
                db, mode="demo", repository="example/repo", source=broken, reference=A
            )
        assert (await snapshot(db))["dataset"] == value["dataset"]
        assert "never-log" not in (await snapshot(db))["latestRun"]["error"]

    asyncio.run(fixture_db(scenario))


def test_demo_and_live_cannot_be_mixed():
    async def scenario(db, *_):
        await publish(db)

        async def unused():
            pytest.fail("Mode mismatch must be rejected before HTTP")

        with pytest.raises(ValueError, match="dataset"):
            await store().refresh(db, mode="live", repository="example/repo", source=unused)

    asyncio.run(fixture_db(scenario))


def test_metrics_week_year_boundaries_bucket_edges_and_odd_median():
    async def scenario(db, *_):
        issues = [
            item(n, created_at=(A - timedelta(days=d)).isoformat(), updated_at=A.isoformat())
            for n, d in enumerate([0, 7, 30, 90], 1)
        ]
        pulls = []
        for n, merged in enumerate(
            ["2025-11-09T23:59:59Z", "2025-11-10T00:00:00Z", "2025-12-29T00:00:00Z", A.isoformat()],
            5,
        ):
            when = datetime.fromisoformat(merged.replace("Z", "+00:00"))
            pulls.append(
                item(
                    n,
                    state="closed",
                    created_at=(when - timedelta(hours=3)).isoformat(),
                    updated_at=merged,
                    closed_at=merged,
                    merged_at=merged,
                )
            )
        await publish(db, issues, pulls)
        value = await snapshot(db)
        assert value["ages"] == [1, 1, 1, 1]
        assert value["metrics"]["mergedPRs"] == 2
        assert value["metrics"]["medianMergeHours"] == 3
        assert value["weeks"][0]["count"] == 1
        assert value["weeks"][7]["count"] == 1
        await publish(
            db,
            issues,
            pulls[:3]
            + [
                item(
                    20,
                    state="closed",
                    created_at="2026-01-04T00:00:00Z",
                    updated_at="2026-01-04T05:00:00Z",
                    closed_at="2026-01-04T05:00:00Z",
                    merged_at="2026-01-04T05:00:00Z",
                )
            ],
        )
        assert (await snapshot(db))["metrics"]["medianMergeHours"] == 3

    asyncio.run(fixture_db(scenario))


def test_search_filters_pagination_and_sql_injection_are_table_only():
    async def scenario(db, *_):
        await publish(db, [item(n) for n in range(1, 26)], [])
        first = await snapshot(db)
        assert len(first["rows"]) == 10
        page = await snapshot(db, "", "", "", 99, "updated")
        assert page["page"] == 3
        assert len(page["rows"]) == 5
        search = await snapshot(db, "#12", "issue", "open", 1, "created")
        assert search["total"] == 1
        assert search["metrics"] == first["metrics"]
        attack = await snapshot(db, "'; DROP TABLE work_items;--", "", "", 1, "updated")
        assert attack["total"] == 0
        assert await db.fetchval("SELECT count(*) FROM work_items") == 25

    asyncio.run(fixture_db(scenario))
