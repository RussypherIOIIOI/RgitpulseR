#!/bin/sh
set -eu
python -m gitpulse.cli migrate
if [ "${GITPULSE_MODE:-demo}" = "demo" ]; then
  python -m gitpulse.cli import
fi
exec node node_modules/next/dist/bin/next start --hostname 0.0.0.0 --port 3000
