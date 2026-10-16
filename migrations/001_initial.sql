-- Additive initial schema. Apply only to a dedicated GitPulse database.
CREATE TABLE import_runs (
    id uuid PRIMARY KEY,
    mode text NOT NULL CHECK (mode IN ('demo', 'live')),
    repository text NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    finished_at timestamptz,
    as_of timestamptz,
    fetched integer NOT NULL DEFAULT 0 CHECK (fetched >= 0),
    written integer NOT NULL DEFAULT 0 CHECK (written >= 0),
    error text
);
CREATE TABLE repositories (
    id integer PRIMARY KEY CHECK (id = 1),
    github_id bigint NOT NULL CHECK (github_id > 0),
    full_name text NOT NULL,
    mode text NOT NULL CHECK (mode IN ('demo', 'live')),
    last_successful_run_id uuid NOT NULL REFERENCES import_runs(id)
);
CREATE TABLE work_items (
    repository_id integer NOT NULL REFERENCES repositories(id),
    number integer NOT NULL CHECK (number > 0),
    source_id bigint NOT NULL CHECK (source_id > 0),
    kind text NOT NULL CHECK (kind IN ('issue', 'pr')),
    title text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 1024),
    author text,
    state text NOT NULL CHECK (state IN ('open', 'closed')),
    url text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL CHECK (updated_at >= created_at),
    closed_at timestamptz,
    merged_at timestamptz,
    last_seen_run_id uuid NOT NULL REFERENCES import_runs(id),
    PRIMARY KEY (repository_id, number),
    UNIQUE (repository_id, kind, source_id),
    CHECK ((state = 'closed') = (closed_at IS NOT NULL)),
    CHECK (closed_at IS NULL OR closed_at BETWEEN created_at AND updated_at),
    CHECK (merged_at IS NULL OR (kind = 'pr' AND state = 'closed'
        AND merged_at BETWEEN created_at AND closed_at))
);
CREATE INDEX work_items_published ON work_items(last_seen_run_id, updated_at DESC, number DESC);
CREATE INDEX import_runs_started ON import_runs(started_at DESC);

-- One statement snapshot: all metrics, audit state and table rows use the same published run.
CREATE FUNCTION gitpulse_dashboard(
    search text DEFAULT '', item_type text DEFAULT '', item_state text DEFAULT '',
    page_number integer DEFAULT 1, sort_field text DEFAULT 'updated'
) RETURNS jsonb LANGUAGE sql STABLE AS $$
WITH published AS (
    SELECT r.*, i.as_of, i.finished_at, i.id AS run_id,
        date_trunc('week', i.as_of AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
            - interval '11 weeks' AS window_start
    FROM repositories r JOIN import_runs i ON i.id = r.last_successful_run_id
), items AS (
    SELECT w.*, CASE WHEN merged_at IS NOT NULL THEN 'merged' ELSE state END AS display_state
    FROM work_items w JOIN published p ON w.last_seen_run_id = p.run_id
), merges AS (
    SELECT i.* FROM items i CROSS JOIN published p
    WHERE kind = 'pr' AND merged_at >= p.window_start AND merged_at < p.as_of
), ages AS (
    SELECT extract(epoch FROM (p.as_of - i.created_at)) / 86400 AS days
    FROM items i CROSS JOIN published p WHERE kind = 'issue' AND state = 'open'
), weeks AS (
    SELECT week, (SELECT count(*) FROM merges m
        WHERE m.merged_at >= week AND m.merged_at < week + interval '1 week') AS count,
        week = p.window_start + interval '11 weeks' AS partial
    FROM published p CROSS JOIN LATERAL generate_series(
        p.window_start, p.window_start + interval '11 weeks', interval '1 week') week
), filtered AS (
    SELECT * FROM items WHERE (search = '' OR strpos(lower(title), lower(search)) > 0
        OR strpos(lower(coalesce(author, '')), lower(search)) > 0
        OR strpos(number::text, ltrim(search, '#')) > 0)
        AND (item_type = '' OR kind = item_type)
        AND (item_state = '' OR display_state = item_state)
), totals AS (SELECT count(*) AS count FROM filtered), paging AS (
    SELECT count, least(greatest(page_number, 1), greatest(1, ceil(count / 10.0)::integer)) AS page
    FROM totals
), page_items AS (
    SELECT * FROM filtered ORDER BY
        CASE WHEN sort_field = 'created' THEN created_at ELSE updated_at END DESC,
        number DESC LIMIT 10 OFFSET (SELECT (page - 1) * 10 FROM paging)
)
SELECT jsonb_build_object(
    'dataset', (SELECT jsonb_build_object('repository', full_name, 'mode', mode,
        'asOf', as_of, 'lastSuccess', finished_at, 'runId', run_id,
        'windowStart', window_start) FROM published),
    'latestRun', (SELECT jsonb_build_object('status', status, 'error', error,
        'startedAt', started_at, 'finishedAt', finished_at, 'written', written)
        FROM import_runs ORDER BY started_at DESC, id DESC LIMIT 1),
    'metrics', jsonb_build_object(
        'medianMergeHours', (SELECT percentile_cont(0.5) WITHIN GROUP
            (ORDER BY extract(epoch FROM (merged_at - created_at)) / 3600) FROM merges),
        'medianIssueDays', (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY days) FROM ages),
        'openIssues', (SELECT count(*) FROM ages),
        'mergedPRs', (SELECT count(*) FROM merges)),
    'weeks', coalesce((SELECT jsonb_agg(jsonb_build_object('week', week, 'count', count,
        'partial', partial) ORDER BY week) FROM weeks), '[]'::jsonb),
    'ages', (SELECT jsonb_build_array(
        count(*) FILTER (WHERE days >= 0 AND days < 7),
        count(*) FILTER (WHERE days >= 7 AND days < 30),
        count(*) FILTER (WHERE days >= 30 AND days < 90),
        count(*) FILTER (WHERE days >= 90)) FROM ages),
    'rows', coalesce((SELECT jsonb_agg(to_jsonb(p)) FROM page_items p), '[]'::jsonb),
    'total', (SELECT count FROM paging), 'page', (SELECT page FROM paging)
);
$$;
