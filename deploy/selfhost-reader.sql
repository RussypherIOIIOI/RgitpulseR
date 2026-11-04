-- Owner-run only, AFTER migrations. Never mount under /docker-entrypoint-initdb.d.
-- psql -X -q -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo -f /opt/gitpulse/selfhost-reader.sql
-- Caller must export GITPULSE_READER_PASSWORD from /run/secrets/reader_password.
\set ON_ERROR_STOP on
\getenv reader_password GITPULSE_READER_PASSWORD
BEGIN;
-- format %L quotes the secret as a SQL literal. An existing role is not rotated.
SELECT format('CREATE ROLE gitpulse_reader LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', :'reader_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gitpulse_reader')
\gexec
-- Refuse an unexpectedly privileged existing identity instead of repurposing it.
DO $$
DECLARE
  reader_oid oid := 'gitpulse_reader'::regrole;
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'gitpulse_reader'
      AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
    OR EXISTS (SELECT FROM pg_auth_members WHERE member = reader_oid)
    -- pg_shdepend ownership dependencies cover every local object class, not
    -- just tables. Shared ownership includes databases and tablespaces.
    -- https://www.postgresql.org/docs/18/catalog-pg-shdepend.html
    OR EXISTS (
      SELECT FROM pg_shdepend
      WHERE refclassid = 'pg_authid'::regclass AND refobjid = reader_oid
        AND deptype = 'o'
        AND (dbid = 0 OR dbid = (SELECT oid FROM pg_database
                                WHERE datname = current_database()))
    )
    -- These inquiry functions include effective privileges inherited through
    -- PUBLIC. The column check also detects grants absent at table level.
    -- https://www.postgresql.org/docs/18/functions-info.html
    OR has_database_privilege(reader_oid, current_database(), 'CREATE')
    OR EXISTS (
      SELECT FROM pg_namespace
      WHERE has_schema_privilege(reader_oid, oid, 'CREATE')
    )
    OR EXISTS (
      SELECT FROM (VALUES ('public.import_runs'::regclass),
                          ('public.repositories'::regclass),
                          ('public.work_items'::regclass)) AS canonical(table_oid)
      WHERE has_table_privilege(reader_oid, table_oid,
              'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
         OR has_any_column_privilege(reader_oid, table_oid,
              'INSERT,UPDATE,REFERENCES')
    )
  THEN
    RAISE EXCEPTION 'Existing gitpulse_reader has elevated privileges; operator review required';
  END IF;
END
$$;
GRANT CONNECT ON DATABASE gitpulse_demo TO gitpulse_reader;
GRANT USAGE ON SCHEMA public TO gitpulse_reader;
REVOKE ALL ON TABLE public.import_runs, public.repositories, public.work_items FROM gitpulse_reader;
GRANT SELECT ON TABLE public.import_runs, public.repositories, public.work_items TO gitpulse_reader;
GRANT EXECUTE ON FUNCTION public.gitpulse_dashboard(text, text, text, integer, text) TO gitpulse_reader;
COMMIT;
