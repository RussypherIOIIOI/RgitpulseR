"""Owner token entry accepts copy-button commands without ever executing them."""

import base64
import json
from pathlib import Path
import shutil
import subprocess

import pytest


TOKEN = base64.b64encode(
    json.dumps(
        {
            "a": "a" * 32,
            "t": "00000000-0000-4000-8000-000000000001",
            "s": "synthetic-test-secret-not-a-real-credential",
        }
    ).encode()
).decode()
MODULE = Path(__file__).resolve().parents[1] / "scripts" / "selfhost-token.ps1"


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def parse_entry(tmp_path, entry):
    assert MODULE.is_file(), "Shared private token parser is missing"
    assert shutil.which("pwsh"), "PowerShell 7 is required for the owner-entry regression contract"
    source, target = tmp_path / "entry.txt", tmp_path / "result.txt"
    source.write_text(entry, encoding="utf-8")
    script = (
        f". {ps_literal(MODULE)}; try {{ "
        f"$token=ConvertFrom-CloudflareTunnelEntry ([IO.File]::ReadAllText({ps_literal(source)})); "
        f"[IO.File]::WriteAllText({ps_literal(target)},$token); Write-Output 'accepted' "
        "} catch { Write-Error $_.Exception.Message; exit 1 }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", script],
        shell=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert TOKEN not in result.stdout + result.stderr, "Parser exposed its secret"
    return result, target


@pytest.mark.parametrize(
    "entry",
    [
        TOKEN,
        f"docker run cloudflare/cloudflared:latest tunnel --no-autoupdate run --token {TOKEN}",
        f'docker run cloudflare/cloudflared:2026.10.7 tunnel run --token="{TOKEN}"',
        f"docker run cloudflare/cloudflared:latest tunnel run --token\r\n'{TOKEN}'",
    ],
)
def test_private_entry_extracts_only_token(tmp_path, entry):
    result, target = parse_entry(tmp_path, entry)
    assert result.returncode == 0, result.stderr
    assert target.read_text() == TOKEN


@pytest.mark.parametrize(
    "entry, reason",
    [
        ("d2100870-8492-4f08-b99c-c6cdb0c6aa37", "Tunnel ID"),
        (
            "docker run cloudflare/cloudflared tunnel run --token eyJhIjoi****************aiJ9",
            "masked",
        ),
        ("docker run cloudflare/cloudflared tunnel run", "valid"),
        ("", "valid"),
        ("a" * 64, "valid"),
    ],
)
def test_invalid_entries_do_not_produce_a_secret_file(tmp_path, entry, reason):
    result, target = parse_entry(tmp_path, entry)
    assert result.returncode != 0
    assert reason.lower() in result.stderr.lower()
    assert not target.exists()
