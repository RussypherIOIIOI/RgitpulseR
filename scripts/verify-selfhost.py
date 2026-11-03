"""Exercise the selfhost package in disposable Docker resources; never start its tunnel."""

import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Already built GitPulse image")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    project = "gitpulse-selfhost-test-" + uuid.uuid4().hex[:12]
    folder = root / "artifacts" / project
    folder.mkdir(parents=True)
    owner, reader = secrets.token_hex(32), secrets.token_hex(32)
    values = {
        "owner_password": owner,
        "reader_password": reader,
        "owner_database_url": f"postgresql://gitpulse_owner:{owner}@db:5432/gitpulse_demo",
        "reader_database_url": f"postgresql://gitpulse_reader:{reader}@db:5432/gitpulse_demo",
        "cloudflared_token": "test-only-never-used-by-a-tunnel-" + secrets.token_hex(24),
    }
    for name, value in values.items():
        target = folder / name
        target.write_text(value, encoding="utf-8")
        # Disposable fixture only: Linux UID 10001 must read a file-bound secret.
        # Production Windows secrets use the ACL-protected owner setup script.
        target.chmod(0o444)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(
        os.environ,
        GITPULSE_IMAGE=args.image,
        GITPULSE_SECRETS_DIR=str(folder),
        GITPULSE_WEB_PORT=str(port),
        GITPULSE_ORIGIN="https://gitpulse.tmcsolutions-org.net",
    )
    compose = [
        "docker",
        "compose",
        "--project-name",
        project,
        "--env-file",
        "deploy/selfhost.env.example",
        "-f",
        "deploy/selfhost.compose.yaml",
    ]
    # Environment values take precedence over example values.
    safe_env_file = folder / "test.env"
    safe_env_file.write_text("", encoding="utf-8")
    compose[compose.index("deploy/selfhost.env.example")] = str(safe_env_file)

    def run(*command, allow_failure=False):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
        if any(value in result.stdout + result.stderr for value in values.values()):
            raise RuntimeError("A secret appeared in child output; output withheld")
        if result.returncode and not allow_failure:
            output = result.stdout + result.stderr
            for value in values.values():
                output = output.replace(value, "[redacted]")
            raise RuntimeError(f"Command failed ({result.returncode}): {output[-5000:]}")
        return result

    def dc(*command, **kwargs):
        return run(*compose, *command, **kwargs)

    def sql(statement, database="gitpulse_demo"):
        return dc(
            "exec",
            "-T",
            "db",
            "psql",
            "-X",
            "-A",
            "-t",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "gitpulse_owner",
            "-d",
            database,
            "-c",
            statement,
        ).stdout.strip()

    def snapshot(database="gitpulse_demo"):
        return json.loads(
            sql(
                "SELECT json_build_object('dataset',gitpulse_dashboard()->'dataset',"
                "'metrics',gitpulse_dashboard()->'metrics','total',gitpulse_dashboard()->'total',"
                "'runs',(SELECT count(*) FROM import_runs))",
                database,
            )
        )

    def http(path, *, post=False, origin=None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            method="POST" if post else "GET",
            headers={"Origin": origin} if origin else {},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    try:
        missing_secret = run(
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--entrypoint",
            "sh",
            args.image,
            "scripts/start-selfhost.sh",
            "true",
            allow_failure=True,
        )
        assert missing_secret.returncode != 0, "Startup accepted a missing DSN file"
        dc("--profile", "operations", "--profile", "public", "config", "--quiet")
        config = json.loads(dc("config", "--format", "json").stdout)
        assert not config["services"]["db"].get("ports"), "Database must have no host port"
        assert config["services"]["app"]["ports"][0]["host_ip"] == "127.0.0.1"
        assert {s["source"] for s in config["services"]["app"]["secrets"]} == {
            "reader_database_url"
        }
        dc("up", "-d", "--wait", "db")
        assert sql("SELECT count(*) FROM pg_tables WHERE schemaname='public'") == "0"
        # Node startup must not run migrations, even when health is unavailable.
        dc("up", "-d", "app")
        deadline = time.monotonic() + 45
        while True:
            try:
                assert http("/api/health") == 503
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
        assert sql("SELECT count(*) FROM pg_tables WHERE schemaname='public'") == "0"
        for command in ("migrate", "import"):
            dc(
                "--profile",
                "operations",
                "run",
                "--rm",
                "bootstrap",
                "python",
                "-m",
                "gitpulse.cli",
                command,
            )
        grant = (
            'export GITPULSE_READER_PASSWORD="$(cat /run/secrets/reader_password)"; '
            "exec psql -X -q -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo "
            "-f /opt/gitpulse/selfhost-reader.sql"
        )
        dc("exec", "-T", "db", "sh", "-c", grant)
        dc("exec", "-T", "db", "sh", "-c", grant)  # Grants repeat without rotating identity.
        # Refuse repurposing an identity with ownership or inherited write access.
        for setup, cleanup in (
            (
                "CREATE TABLE public.reader_owned_guard(id integer); "
                "ALTER TABLE public.reader_owned_guard OWNER TO gitpulse_reader",
                "DROP TABLE public.reader_owned_guard",
            ),
            (
                "GRANT CREATE ON SCHEMA public TO gitpulse_reader",
                "REVOKE CREATE ON SCHEMA public FROM gitpulse_reader",
            ),
            (
                "GRANT UPDATE ON public.work_items TO PUBLIC",
                "REVOKE UPDATE ON public.work_items FROM PUBLIC",
            ),
            (
                "GRANT UPDATE(title) ON public.work_items TO gitpulse_reader",
                "REVOKE UPDATE(title) ON public.work_items FROM gitpulse_reader",
            ),
        ):
            sql(setup)
            try:
                refused = dc("exec", "-T", "db", "sh", "-c", grant, allow_failure=True)
                assert refused.returncode != 0, "Unsafe existing reader identity was accepted"
            finally:
                sql(cleanup)
        dc("exec", "-T", "db", "sh", "-c", grant)
        dc("up", "-d", "--wait", "--wait-timeout", "100", "app")
        before = snapshot()
        assert before["total"] == 44 and before["runs"] == 1
        assert before["metrics"] == {
            "mergedPRs": 15,
            "openIssues": 20,
            "medianIssueDays": 14,
            "medianMergeHours": 7,
        }
        reader_check = """
const assert = require('node:assert/strict');
const {Client} = require('pg');
(async () => {
  const db = new Client({connectionString: process.env.DATABASE_URL});
  await db.connect();
  assert.equal((await db.query('SELECT current_user')).rows[0].current_user, 'gitpulse_reader');
  assert.equal((await db.query('SELECT gitpulse_dashboard() AS s')).rows[0].s.total, 44);
  for (const q of ['UPDATE work_items SET title=title WHERE false',
                   'CREATE TABLE public.unexpected_write (id integer)']) {
    await assert.rejects(db.query(q), e => e.code === '42501');
  }
  await db.end();
})().catch(e => { console.error(e.code || e.name); process.exit(1); });
"""
        dc("exec", "-T", "app", "sh", "scripts/start-selfhost.sh", "node", "-e", reader_check)
        assert http("/api/health") == 200
        assert http("/api/refresh", post=True) == 403
        assert http("/api/refresh", post=True, origin="https://unrelated.example") == 403
        dc("restart", "app")
        dc("up", "-d", "--wait", "--wait-timeout", "100", "app")
        assert snapshot() == before, "Restart changed publication"
        # Backup/restore stays inside this disposable project's private database.
        dc(
            "exec",
            "-T",
            "db",
            "pg_dump",
            "-U",
            "gitpulse_owner",
            "-d",
            "gitpulse_demo",
            "-Fc",
            "-f",
            "/tmp/gitpulse-test.dump",
        )
        dc("exec", "-T", "db", "createdb", "-U", "gitpulse_owner", "gitpulse_recovery_test")
        dc(
            "exec",
            "-T",
            "db",
            "pg_restore",
            "-U",
            "gitpulse_owner",
            "--exit-on-error",
            "--no-owner",
            "-d",
            "gitpulse_recovery_test",
            "/tmp/gitpulse-test.dump",
        )
        assert snapshot("gitpulse_recovery_test") == before, "Restored snapshot differs"
        names = dc("ps", "--services", "--status", "running").stdout.splitlines()
        assert "tunnel" not in names, "Test must not start public tunnel"
        print(
            "Selfhost contracts PASS: no implicit SQL, reader denies writes, exact metrics, "
            "refresh rejection, restart persistence, isolated backup/restore; no public tunnel."
        )
    finally:
        # Only this script's freshly generated disposable project may be removed.
        assert project.startswith("gitpulse-selfhost-test-") and len(project) == 35
        dc("down", "--volumes", "--remove-orphans", allow_failure=True)


if __name__ == "__main__":
    main()
