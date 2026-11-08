import Link from "next/link";
import type { CSSProperties } from "react";
import { dashboard, type Snapshot } from "../lib/data";
import { parseFilters, type Filters } from "../lib/filters";
import { Icon } from "./_components/brand";
import { Frame, MethodBand, PatternStrip, REPOSITORY_URL } from "./_components/site";
import RefreshControls from "./refresh-controls";

export const dynamic = "force-dynamic";
const date = (value: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
}).format(new Date(value));
const shortDate = (value: string) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const timestamp = (value: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
  hour12: false, timeZone: "UTC",
}).format(new Date(value)) + " UTC";
const number = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
const index = (i: number) => ({ "--i": i }) as CSSProperties;

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="notice" role="alert"><strong>{title}</strong><div>{children}</div></section>;
}

/** Recovery states keep the site chrome and a single page heading. */
function StatePage({ children, enabled }: { children: React.ReactNode; enabled?: boolean }) {
  return <Frame nav={false}><section className="band state-band"><div className="band-inner">
    <div className="section-heading"><div><p className="eyebrow">Dashboard</p><h1>Repository overview</h1></div>
      {enabled === undefined ? null : <RefreshControls enabled={enabled} />}</div>
    {children}
  </div></section></Frame>;
}

/** Hero art: an LED field built from the real weekly merge counts. Lit dots scale to the busiest week. */
function Pulse({ data }: { data: Snapshot }) {
  const rows = 8;
  const max = Math.max(1, ...data.weeks.map(w => w.count));
  const busiest = Math.max(0, ...data.weeks.map(w => w.count));
  const first = data.weeks[0], last = data.weeks.at(-1);
  return <figure className="pulse" aria-labelledby="pulse-caption">
    <div className="pulse-head"><span className="pulse-repo">{data.dataset?.repository}</span>
      <span className="pulse-live"><span className="status-dot" aria-hidden="true" />Snapshot</span></div>
    <div className="pulse-readout" aria-hidden="true"><span>Merged · 12 wk</span><b>{data.metrics.mergedPRs}</b></div>
    <div className="pulse-field" aria-hidden="true">
      {data.weeks.map((w, col) => {
        const lit = w.count ? Math.max(1, Math.round(w.count / max * rows)) : 0;
        return <span className={`pulse-col${w.partial ? " partial" : ""}`} key={w.week} style={index(col)}>
          {Array.from({ length: rows }, (_, row) => <i key={row} className={row < lit ? "on" : undefined} style={{ "--r": row } as CSSProperties} />)}
        </span>;
      })}
      <span className="pulse-sweep" />
    </div>
    <div className="pulse-axis" aria-hidden="true"><span>{first ? shortDate(first.week) : ""}</span><span>{last ? `${shortDate(last.week)}${last.partial ? " · partial" : ""}` : ""}</span></div>
    <figcaption id="pulse-caption">{data.metrics.mergedPRs} pull requests merged across {data.weeks.length} UTC weeks;
      the busiest week merged {busiest}. Each column is one week; the violet-ringed column is the current, partial week.</figcaption>
  </figure>;
}

function Hero({ data }: { data: Snapshot }) {
  const m = data.metrics;
  const ledger: [string, string][] = [
    ["Merged PRs · 12 wk", String(m.mergedPRs)],
    ["Open issues", String(m.openIssues)],
    ["Median merge", m.medianMergeHours === null ? "—" : `${number(m.medianMergeHours)} h`],
    ["Median issue age", m.medianIssueDays === null ? "—" : `${number(m.medianIssueDays)} d`],
  ];
  return <section className="band hero" aria-labelledby="hero-title">
    <div className="band-inner hero-grid">
      <div className="hero-copy">
        <p className="eyebrow">Portfolio project · Repository observatory</p>
        <h1 id="hero-title" className="display">GitHub activity, published as <span className="display-accent">numbers you can explain.</span></h1>
        <p className="hero-lead">GitPulse imports one repository’s issues and pull requests, publishes them to PostgreSQL as a single
          validated snapshot, and reports three plain signals: how long merges take, how long issues stay open, and how much
          ships each week.</p>
        <div className="hero-actions">
          <a className="btn btn-primary" href="#overview">Explore the dashboard</a>
          <a className="btn" href={REPOSITORY_URL}><Icon name="document" size={16} />Source on GitHub</a>
        </div>
        <dl className="ledger hero-ledger">{ledger.map(([term, value]) => <div key={term}><dt>{term}</dt><dd>{value}</dd></div>)}</dl>
        <p className="ledger-note">Read from the published snapshot on every request.</p>
      </div>
      <div className="hero-art"><Pulse data={data} /></div>
    </div>
  </section>;
}

function Charts({ data }: { data: Snapshot }) {
  const max = Math.max(1, ...data.weeks.map(w => w.count));
  const ageMax = Math.max(1, ...data.ages);
  return <div className="charts">
    <section className="panel weekly" aria-labelledby="weekly-title">
      <div className="panel-heading"><div><p className="eyebrow">Throughput</p><h3 id="weekly-title">Pull requests merged</h3>
        <p>Weekly · Last 12 UTC weeks</p></div><span className="chart-total">{data.metrics.mergedPRs}<small>total merged</small></span></div>
      <div className="bar-chart" role="img" aria-label={`Weekly merged pull requests, oldest first: ${data.weeks.map(w => `${date(w.week)}: ${w.count}${w.partial ? ", partial week" : ""}`).join("; ")}`}>
        <span className="gridlines" aria-hidden="true"><i /><i /><i /><i /></span>
        {data.weeks.map((w, i) => <div className="bar-column" key={w.week}>
          <div className="bar-space"><span className={`bar ${w.partial ? "partial" : ""}`}
            style={{ height: `${w.count / max * 82}%`, minHeight: w.count ? 8 : 2 }}><b>{w.count}</b></span></div>
          <span className="bar-label">{i % 3 === 0 || i === data.weeks.length - 1 ? shortDate(w.week) : ""}</span>
        </div>)}
      </div>
      <p className="chart-note"><span className="legend-square" />Merged PRs <span className="legend-partial" />Current week (partial)</p>
    </section>
    <section className="panel" aria-labelledby="age-title"><div className="panel-heading"><div>
      <p className="eyebrow">Backlog</p><h3 id="age-title">How long have issues been open?</h3><p>Age since creation · All open issues</p></div></div>
      <div className="age-chart" role="img" aria-label={`Open issue ages: ${["under 7", "7 to under 30", "30 to under 90", "90 or more"].map((v, i) => `${v} days: ${data.ages[i]}`).join("; ")}`}>
        {["Under 7 days", "7–29 days", "30–89 days", "90+ days"].map((label, i) =>
          <div className="age-row" key={label}><span>{label}</span><div className="age-track"><span style={{ width: `${data.ages[i] / ageMax * 100}%` }} /></div><b>{data.ages[i]}</b></div>)}
      </div><p className="chart-note">Includes reopened issues. Excludes pull requests.</p>
    </section>
  </div>;
}

function Activity({ data, filters }: { data: Snapshot; filters: Filters }) {
  const pages = Math.max(1, Math.ceil(data.total / 10));
  const href = (page: number) => "/?" + new URLSearchParams({ q: filters.q, type: filters.type,
    state: filters.state, sort: filters.sort, page: String(page) }).toString() + "#activity";
  return <section id="activity" className="panel activity" aria-labelledby="activity-title">
    <div className="panel-heading"><div><p className="eyebrow">Records</p>
      <h3 id="activity-title">Repository activity <span className="count-chip">{data.total}</span></h3>
      <p>One row per issue or pull request, in its current imported state.</p></div></div>
    <form className="filters" action="/#activity">
      <div className="search-field"><label htmlFor="q">Search activity</label><input id="q" name="q" type="search"
        placeholder="Search title, #number, or author" defaultValue={filters.q} maxLength={200} /></div>
      <div><label htmlFor="type">Type</label><select id="type" name="type" defaultValue={filters.type}>
        <option value="">All types</option><option value="issue">Issues</option><option value="pr">Pull requests</option></select></div>
      <div><label htmlFor="state">State</label><select id="state" name="state" defaultValue={filters.state}>
        <option value="">All states</option><option value="open">Open</option><option value="closed">Closed</option><option value="merged">Merged</option></select></div>
      <div><label htmlFor="sort">Sort by</label><select id="sort" name="sort" defaultValue={filters.sort}>
        <option value="updated">Recently updated</option><option value="created">Recently created</option></select></div>
      <div className="filter-actions"><button className="btn btn-primary" type="submit">Apply filters</button>
        <Link className="clear" href="/#activity">Clear filters</Link></div>
    </form>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Repository activity table">
      <table><caption className="sr-only">Current issues and pull requests. Filters affect this table only.</caption>
        <thead><tr><th scope="col">Type / #</th><th scope="col">Title</th><th scope="col">Author</th><th scope="col">State</th><th scope="col">Created (UTC)</th><th scope="col">Updated (UTC)</th></tr></thead>
        <tbody>{data.rows.map(row => <tr key={row.number} data-testid="activity-row">
          <td><span className={`item-icon ${row.kind}`}><Icon name={row.kind === "pr" ? "action" : "record"} size={16} /></span><span className="sr-only">{row.kind === "pr" ? "Pull request" : "Issue"} </span><span className="item-number">#{row.number}</span></td>
          <td><a href={row.url} target="_blank" rel="noreferrer">{row.title}<span className="sr-only"> (opens GitHub in a new tab)</span></a></td>
          <td className="author">{row.author ?? "Deleted author"}</td><td><span className={`state ${row.display_state}`}>{row.display_state}</span></td>
          <td><time dateTime={row.created_at}>{date(row.created_at)}</time></td><td><time dateTime={row.updated_at}>{date(row.updated_at)}</time></td>
        </tr>)}</tbody></table>
      {data.total === 0 ? <p className="empty-table">No activity matches these filters.</p> : null}
    </div><div className="pagination"><span>{data.total ? `${(data.page-1)*10+1}–${Math.min(data.page*10,data.total)} of ${data.total} records` : "0 records"}</span>
      <div>{data.page > 1 ? <Link className="btn btn-sm" aria-label="Previous page" href={href(data.page-1)}>Previous</Link> : <span className="btn btn-sm" aria-disabled="true">Previous</span>}
        <span>Page {data.page} of {pages}</span>{data.page < pages ? <Link className="btn btn-sm" aria-label="Next page" href={href(data.page+1)}>Next</Link> : <span className="btn btn-sm" aria-disabled="true">Next</span>}</div></div>
    <p className="table-note">Search and filters affect the table only. Metrics above keep their full populations.</p>
  </section>;
}

export default async function Page({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  let filters: Filters;
  try { filters = parseFilters(await searchParams); }
  catch { return <StatePage><Notice title="Invalid table filters"><p>Choose a valid page, type, state, or sort order.</p><Link href="/">Reset filters</Link></Notice></StatePage>; }
  let data: Snapshot;
  try { data = await dashboard(filters); }
  catch { return <StatePage><Notice title="Database unavailable"><p>The dashboard could not read the configured dataset. Check the database connection and migration, then reload.</p><Link href="/">Try again</Link></Notice></StatePage>; }
  const dataset = data.dataset;
  const enabled = process.env.GITPULSE_REFRESH_ENABLED === "true";
  if (!dataset) return <StatePage enabled={enabled}><Notice title="No successful import yet"><p>Run the configured import from the project CLI, or use the maintainer controls.</p></Notice>
    {data.latestRun?.status === "failed" ? <Notice title="Latest refresh failed"><p>{data.latestRun.error}</p></Notice> : null}</StatePage>;
  const demo = dataset.mode === "demo";
  const m = data.metrics;
  return <Frame status={demo ? "Demo dataset" : "Live dataset"}>
    <Hero data={data} />
    <PatternStrip />
    <section id="overview" className="band dashboard" aria-labelledby="overview-title">
      <div className="band-inner">
        <div className="section-heading"><div><p className="eyebrow">Dashboard</p><h2 id="overview-title">Repository overview</h2>
          <p>A little signal. A lot less guesswork.</p></div><RefreshControls enabled={enabled} /></div>
        <div className="repository-strip">
          <div><span className="repository-symbol"><Icon name="database" /></span><div><p className="repository-name">{dataset.repository}</p>
            {demo ? <p>Synthetic repository · Deterministic sample data</p> : <a href={`https://github.com/${dataset.repository}`} target="_blank" rel="noreferrer">View source on GitHub<span className="sr-only"> (opens in a new tab)</span></a>}</div></div>
          <span className={`mode ${demo ? "demo" : "live"}`}>{demo ? "Synthetic demo" : "Live data"}</span></div>
        <div className="freshness"><span><span className="connection-dot" aria-hidden="true" />Last successful load <time data-testid="last-success" dateTime={dataset.lastSuccess}>{timestamp(dataset.lastSuccess)}</time></span>
          <span>Dataset reference <time dateTime={dataset.asOf}>{timestamp(dataset.asOf)}</time></span></div>
        {demo ? <p className="demo-note"><Icon name="signal" size={16} />You’re exploring a synthetic dataset fixed at {date(dataset.asOf)}. A new load updates the load time; the sample metrics stay reproducible.</p> : null}
        {data.latestRun?.status === "failed" ? <Notice title="Latest refresh failed"><p>{data.latestRun.error} Showing the last successful dataset.</p></Notice> : null}
        {data.latestRun?.status === "running" ? <p className="demo-note"><Icon name="pipeline" size={16} />Refresh in progress. Showing the last successful dataset until publication completes.</p> : null}
        {data.stale ? <Notice title="Dataset is more than 24 hours old"><p>Run a refresh to collect more recent repository activity.</p></Notice> : null}
        <div className="kpis">
          <div className="kpi"><p><Icon name="action" size={16} />Median time to merge</p>
            <div className="metric" data-testid="merge-median">{m.medianMergeHours === null ? "—" : number(m.medianMergeHours)}<small>{m.medianMergeHours === null ? "" : "hours"}</small></div>
            <span>{m.medianMergeHours === null ? "No merged pull requests" : "From creation to merge · 12 UTC weeks"}</span></div>
          <div className="kpi"><p><Icon name="calendar" size={16} />Median open-issue age</p>
            <div className="metric">{m.medianIssueDays === null ? "—" : number(m.medianIssueDays)}<small>{m.medianIssueDays === null ? "" : "days"}</small></div>
            <span>{m.medianIssueDays === null ? "No open issues" : "Since creation · Full imported history"}</span></div>
          <div className="kpi"><p><Icon name="record" size={16} />Open issues</p>
            <div className="metric" data-testid="open-count">{m.openIssues}</div><span>True issues only · Pull requests excluded</span></div>
        </div>
        <Charts data={data} /><Activity data={data} filters={filters} />
      </div>
    </section>
    <MethodBand demo={demo} readOnly={!enabled} />
  </Frame>;
}
