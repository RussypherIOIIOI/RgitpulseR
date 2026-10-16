import importlib
import json
import os
import subprocess
import sys

import pytest


def test_bundled_demo_is_deterministic_valid_and_large_enough_to_paginate():
    assert importlib.util.find_spec("gitpulse.cli"), "The runnable ingestion CLI is missing"
    cli = importlib.import_module("gitpulse.cli")
    from gitpulse.model import normalize

    first = cli.demo_payload()
    second = cli.demo_payload()
    assert first == second
    repo, issues, pulls, as_of = first
    rows = normalize(issues, pulls, as_of, repo["full_name"])
    assert len(rows) > 30
    assert any(r["author"] is None for r in rows)
    assert any(r["merged_at"] for r in rows)
    assert any(r["kind"] == "pr" and r["state"] == "closed" and not r["merged_at"] for r in rows)


def test_cli_missing_configuration_fails_without_exposing_credentials():
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "GITPULSE_MODE")}
    result = subprocess.run(
        [sys.executable, "-m", "gitpulse.cli", "import"], capture_output=True, text=True, env=env
    )
    assert result.returncode != 0
    assert "DATABASE_URL" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "dsn", ["sensitive-dsn-value", "postgresql://u:p@localhost:sensitive-dsn-value/db"]
)
def test_invalid_database_url_never_echoes_its_value(dsn):
    result = subprocess.run(
        [sys.executable, "-m", "gitpulse.cli", "import"],
        capture_output=True,
        text=True,
        env=dict(os.environ, DATABASE_URL=dsn),
    )
    assert result.returncode != 0
    assert "sensitive-dsn-value" not in result.stderr


@pytest.mark.integration
def test_cli_migrate_import_twice_status_and_nonzero_failure():
    url = os.environ.get("TEST_CLI_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_CLI_DATABASE_URL to a separate empty GitPulse database")
    env = dict(os.environ, DATABASE_URL=url, GITPULSE_MODE="demo")
    for command in ("migrate", "migrate", "import", "import", "status"):
        result = subprocess.run(
            [sys.executable, "-m", "gitpulse.cli", command], capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["dataset"]["mode"] == "demo"
    assert data["total"] > 30
    result = subprocess.run(
        [sys.executable, "-m", "gitpulse.cli", "import"],
        capture_output=True,
        text=True,
        env=dict(env, GITPULSE_MODE="live", GITPULSE_REPO="octocat/Hello-World"),
    )
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
