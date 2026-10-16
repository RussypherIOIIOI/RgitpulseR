"""Run from the repository root: gitpulse migrate / import / status."""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from importlib.resources import files
from pathlib import Path

import asyncpg
import httpx

from gitpulse.github import GitHub
from gitpulse.store import RefreshBusy, refresh, safe_error


def demo_payload() -> tuple[dict, list, list, datetime]:
    data = json.loads(files("gitpulse").joinpath("data/demo.json").read_text(encoding="utf-8"))
    return data["repository"], data["issues"], data["pulls"], datetime.fromisoformat(data["as_of"])


async def migrate(db: asyncpg.Connection) -> None:
    async with db.transaction():
        await db.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended('gitpulse:migration:v1',0))"
        )
        existing = await db.fetchval("SELECT to_regclass('repositories')")
        if existing:
            if not await db.fetchval(
                "SELECT to_regprocedure('gitpulse_dashboard(text,text,text,integer,text)')"
            ):
                raise RuntimeError("Incomplete schema; inspect the dedicated GitPulse database")
            return
        await db.execute(Path("migrations/001_initial.sql").read_text(encoding="utf-8"))


async def execute(command: str, cooldown: int = 0) -> dict:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is required")
    db = await asyncpg.connect(
        url, timeout=10, command_timeout=20, server_settings={"timezone": "UTC"}
    )
    try:
        if command == "migrate":
            await migrate(db)
            return {"status": "schema ready", "version": 1}
        if command == "status":
            return json.loads(await db.fetchval("SELECT gitpulse_dashboard()"))
        mode = os.environ.get("GITPULSE_MODE", "demo")
        if mode == "demo":
            repo, issues, pulls, reference = demo_payload()

            async def source():
                return repo, issues, pulls

            return await refresh(
                db,
                mode=mode,
                repository=repo["full_name"],
                source=source,
                reference=reference,
                cooldown=cooldown,
            )
        if mode != "live":
            raise ValueError("GITPULSE_MODE must be demo or live")
        repository = os.environ.get("GITPULSE_REPO", "")
        async with httpx.AsyncClient() as http:
            source = GitHub(http, repository, token=os.environ.get("GITHUB_TOKEN")).collect
            return await refresh(
                db, mode=mode, repository=repository, source=source, cooldown=cooldown
            )
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="GitPulse single-repository ingestion")
    parser.add_argument("command", choices=("migrate", "import", "status"))
    parser.add_argument("--cooldown", type=int, default=0)
    args = parser.parse_args()
    try:

        async def bounded():
            async with asyncio.timeout(150):
                return await execute(args.command, args.cooldown)

        print(json.dumps(asyncio.run(bounded())))
    except RefreshBusy:
        print("Refresh busy or cooling down; retry later", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:
        safe_configuration = {
            "DATABASE_URL is required",
            "GITPULSE_MODE must be demo or live",
            "Configured dataset differs from this database; use a separate database",
        }
        message = str(exc) if str(exc) in safe_configuration else safe_error(exc)
        print(message, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
