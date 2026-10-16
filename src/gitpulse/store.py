"""Session locking and atomic publication; no transaction spans collection."""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import uuid4

import asyncpg

from gitpulse.github import ImportFailure
from gitpulse.model import DataError, normalize

LOCK = "gitpulse:single-dataset:v1"
FIELDS = (
    "number",
    "source_id",
    "kind",
    "title",
    "author",
    "state",
    "url",
    "created_at",
    "updated_at",
    "closed_at",
    "merged_at",
)
Source = Callable[[], Awaitable[tuple[dict, list, list]]]


class RefreshBusy(RuntimeError):
    """Another entry point owns the import, or the cooldown has not elapsed."""


def safe_error(exc: BaseException) -> str:
    if isinstance(exc, (DataError, ImportFailure)):
        return str(exc)
    return "Import failed. Previous published data was preserved; check database and source access."


async def refresh(
    db: asyncpg.Connection,
    *,
    mode: str,
    repository: str,
    source: Source,
    reference: datetime | None = None,
    cooldown: int = 0,
) -> dict:
    if mode not in ("demo", "live"):
        raise ValueError("Invalid dataset mode")
    locked = await db.fetchval("SELECT pg_try_advisory_lock(hashtextextended($1,0))", LOCK)
    if not locked:
        raise RefreshBusy("A refresh is already running")
    run_id = None
    try:
        existing = await db.fetchrow("SELECT * FROM repositories WHERE id=1")
        if existing and (
            existing["mode"] != mode or existing["full_name"].lower() != repository.lower()
        ):
            raise ValueError(
                "Configured dataset differs from this database; use a separate database"
            )
        if cooldown and await db.fetchval(
            "SELECT EXISTS(SELECT 1 FROM import_runs WHERE "
            "started_at > clock_timestamp() - $1 * interval '1 second')",
            cooldown,
        ):
            raise RefreshBusy("Refresh cooldown active; try again in one minute")
        # Owning the session lock proves earlier running attempts no longer own it.
        await db.execute(
            "UPDATE import_runs SET status='failed',finished_at=clock_timestamp(),"
            "error='Previous importer stopped before publication' WHERE status='running'"
        )
        run_id = uuid4()
        await db.execute(
            "INSERT INTO import_runs(id,mode,repository,status) VALUES($1,$2,$3,'running')",
            run_id,
            mode,
            repository,
        )
        repo, issues, pulls = await source()
        as_of = reference or datetime.now(timezone.utc)
        if (
            type(repo.get("id")) is not int
            or repo["id"] <= 0
            or repo.get("private") is not False
            or repo.get("full_name", "").lower() != repository.lower()
        ):
            raise DataError("Repository identity or visibility mismatch")
        if existing and existing["github_id"] != repo["id"]:
            raise DataError("Repository numeric identity changed")
        rows = normalize(issues, pulls, as_of, repository)
        await db.execute(
            "UPDATE import_runs SET fetched=$2 WHERE id=$1", run_id, len(issues) + len(pulls)
        )
        async with db.transaction():
            await db.execute(
                "INSERT INTO repositories VALUES(1,$1,$2,$3,$4) ON CONFLICT(id) DO NOTHING",
                repo["id"],
                repository,
                mode,
                run_id,
            )
            previous = {r["number"]: r for r in await db.fetch("SELECT * FROM work_items")}
            values = []
            for row in rows:
                old = previous.get(row["number"])
                if old:
                    if old["kind"] != row["kind"] or old["source_id"] != row["source_id"]:
                        raise DataError("Conflicting persistent source identity")
                    if old["updated_at"] == row["updated_at"] and any(
                        old[key] != row[key] for key in FIELDS
                    ):
                        raise DataError("Conflicting records at equal source version")
                    if old["updated_at"] > row["updated_at"]:
                        row = dict(old)
                if any(
                    row[key] and row[key] > as_of
                    for key in ("created_at", "updated_at", "closed_at", "merged_at")
                ):
                    raise DataError("Dataset reference precedes retained source timestamps")
                values.append(tuple(row[k] for k in FIELDS) + (run_id,))
            await db.executemany(
                "INSERT INTO work_items(repository_id," + ",".join(FIELDS) + ",last_seen_run_id) "
                "VALUES(1," + ",".join(f"${i}" for i in range(1, 13)) + ") "
                "ON CONFLICT(repository_id,number) DO UPDATE SET "
                + ",".join(f"{key}=excluded.{key}" for key in FIELDS[1:])
                + ",last_seen_run_id=excluded.last_seen_run_id",
                values,
            )
            await db.execute(
                "UPDATE import_runs SET status='success',as_of=$2,written=$3,"
                "finished_at=clock_timestamp() WHERE id=$1",
                run_id,
                as_of,
                len(rows),
            )
            await db.execute("UPDATE repositories SET last_successful_run_id=$1 WHERE id=1", run_id)
        return {
            "status": "success",
            "written": len(rows),
            "runId": str(run_id),
            "asOf": as_of.isoformat(),
        }
    except BaseException as exc:
        if run_id is not None:
            await db.execute(
                "UPDATE import_runs SET status='failed',error=$2,"
                "finished_at=clock_timestamp() WHERE id=$1",
                run_id,
                safe_error(exc),
            )
        raise
    finally:
        await db.execute("SELECT pg_advisory_unlock(hashtextextended($1,0))", LOCK)
