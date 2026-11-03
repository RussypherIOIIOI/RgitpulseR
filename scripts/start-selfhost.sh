#!/bin/sh
set -eu
# Compose mounts a service-specific DSN file; never print its contents.
if [ -z "${DATABASE_URL_FILE:-}" ] || [ ! -r "$DATABASE_URL_FILE" ]; then
  printf '%s\n' 'DATABASE_URL_FILE must name a readable secret file.' >&2
  exit 1
fi
DATABASE_URL=$(cat "$DATABASE_URL_FILE")
if [ -z "$DATABASE_URL" ]; then
  printf '%s\n' 'The database secret file is empty.' >&2
  exit 1
fi
export DATABASE_URL
exec "$@"
