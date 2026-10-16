import Link from "next/link";
import { dashboard, type Snapshot } from "../lib/data";
import { parseFilters, type Filters } from "../lib/filters";
import RefreshControls from "./refresh-controls";

export const dynamic = "force-dynamic";
const date = (value: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
}).format(new Date(value));
const timestamp = (value: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
  hour12: false, timeZone: "UTC",
}).format(new Date(value)) + " UTC";
const number = (value: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);

function Mark() {
  return <svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <path d="M4 17h6l4-10 5 19 4-9h5" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>;
}

function Frame({ children }: { children: React.ReactNode }) {
  return <div className="shell"><a className="skip" href="#main">Skip to content</a>
    <aside className="rail"><Link className="brand" href="/"><Mark />GitPulse</Link>
      <p className="rail-description">A clearer view of your repository.</p>
      <nav aria-label="Main navigation"><a aria-label="Overview" className="nav-active" href="#main">◫ <span>Overview</span></a>
        <a aria-label="Activity" href="#activity">☷ <span>Activity</span></a><a aria-label="How it works" href="#methodology">◎ <span>How it works</span></a></nav>
      <div className="rail-footer"><span className="connection-dot" /> Built for clarity<p>One repository.<br />Explainable metrics.</p></div>
    </aside><div className="workspace"><header className="topbar"><span>Repository observatory</span>
      <span>GitHub activity, in perspective</span></header><main id="main">{children}</main>
      <footer className="footer">GitPulse <span>Built with Python, PostgreSQL &amp; Next.js</span></footer>
    </div></div>;
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="notice" role="alert"><strong>{title}</strong><div>{children}</div></section>;
}

function Charts({ data }: { data: Snapshot }) {
  const max = Math.max(1, ...data.weeks.map(w => w.count));
  const ageMax = Math.max(1, ...data.ages);
  return <div className="charts">
    <section className="panel weekly" aria-labelledby="weekly-title">
      <div className="panel-heading"><div><h2 id="weekly-title">Pull requests merged</h2>
        <p>Weekly throughput · Last 12 UTC weeks</p></div><span className="chart-total">{data.metrics.mergedPRs}<small>total merged</small></span></div>
      <div className="bar-chart" role="img" aria-label={`Weekly merged pull requests, oldest first: ${data.weeks.map(w => `${date(w.week)}: ${w.count}${w.partial ? ', partial week' : ''}`).join('; ')}`}>
        {data.weeks.map((w, i) => <div className="bar-column" key={w.week}>
          <div className="bar-space"><span className={`bar ${w.partial ? "partial" : ""}`}
            style={{ height: `${w.count / max * 82}%`, minHeight: w.count ? 8 : 2 }}><b>{w.count}</b></span></div>
          <span className="bar-label">{i % 2 === 0 || w.partial ? new Date(w.week).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" }) : ""}</span>
        </div>)}
      </div>
      <p className="chart-note"><span className="legend-square" />Merged PRs <span className="current-week">Striped bar: current week (partial)</span></p>
    </section>
    <section className="panel" aria-labelledby="age-title"><div className="panel-heading"><div>
      <h2 id="age-title">How long have issues been open?</h2><p>Age since creation · All open issues</p></div></div>
      <div className="age-chart" role="img" aria-label={`Open issue ages: ${["under 7", "7 to under 30", "30 to under 90", "90 or more"].map((v, i) => `${v} days: ${data.ages[i]}`).join('; ')}`}>
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
    <div className="panel-heading"><div><h2 id="activity-title">Repository activity <span className="count-chip">{data.total}</span></h2>
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
      <button type="submit">Apply filters</button><Link className="clear" href="/#activity">Clear filters</Link>
    </form>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Repository activity table">
      <table><caption className="sr-only">Current issues and pull requests. Filters affect this table only.</caption>
        <thead><tr><th scope="col">Type / #</th><th scope="col">Title</th><th scope="col">Author</th><th scope="col">State</th><th scope="col">Created (UTC)</th><th scope="col">Updated (UTC)</th></tr></thead>
        <tbody>{data.rows.map(row => <tr key={row.number} data-testid="activity-row">
          <td><span className={`item-icon ${row.kind}`}>{row.kind === "pr" ? "⑂" : "⊙"}</span><span className="sr-only">{row.kind === "pr" ? "Pull request" : "Issue"} </span>#{row.number}</td>
          <td><a href={row.url} target="_blank" rel="noreferrer">{row.title}<span className="sr-only"> (opens GitHub in a new tab)</span></a></td>
          <td className="author">{row.author ?? "Deleted author"}</td><td><span className={`state ${row.display_state}`}>{row.display_state}</span></td>
          <td><time dateTime={row.created_at}>{date(row.created_at)}</time></td><td><time dateTime={row.updated_at}>{date(row.updated_at)}</time></td>
        </tr>)}</tbody></table>
      {data.total === 0 ? <p className="empty-table">No activity matches these filters.</p> : null}
    </div><div className="pagination"><span>{data.total ? `${(data.page-1)*10+1}–${Math.min(data.page*10,data.total)} of ${data.total} records` : "0 records"}</span>
      <div>{data.page > 1 ? <Link aria-label="Previous page" href={href(data.page-1)}>Previous</Link> : <span aria-disabled="true">Previous</span>}
        <span>Page {data.page} of {pages}</span>{data.page < pages ? <Link aria-label="Next page" href={href(data.page+1)}>Next</Link> : <span aria-disabled="true">Next</span>}</div></div>
    <p className="table-note">Search and filters affect the table only. Metrics above keep their full populations.</p>
  </section>;
}

export default async function Page({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  let filters: Filters;
  try { filters = parseFilters(await searchParams); }
  catch { return <Frame><Notice title="Invalid table filters"><p>Choose a valid page, type, state, or sort order.</p><Link href="/">Reset filters</Link></Notice></Frame>; }
  let data: Snapshot;
  try { data = await dashboard(filters); }
  catch { return <Frame><Notice title="Database unavailable"><p>The dashboard could not read the configured dataset. Check the database connection and migration, then reload.</p><Link href="/">Try again</Link></Notice></Frame>; }
  const dataset = data.dataset;
  const enabled = process.env.GITPULSE_REFRESH_ENABLED === "true";
  if (!dataset) return <Frame><h1>Repository overview</h1><Notice title="No successful import yet"><p>Run the configured import from the project CLI, or use the maintainer controls.</p></Notice>
    {data.latestRun?.status === "failed" ? <Notice title="Latest refresh failed"><p>{data.latestRun.error}</p></Notice> : null}<RefreshControls enabled={enabled} /></Frame>;
  const demo = dataset.mode === "demo";
  const stale = data.stale;
  return <Frame>
    <div className="page-heading"><div><h1>Repository overview</h1><p>A little signal. A lot less guesswork.</p></div><RefreshControls enabled={enabled} /></div>
    <section className="repository-strip"><div><span className="repository-symbol">⌘</span><div><h2>{dataset.repository}</h2>
      {demo ? <p>Synthetic repository · Deterministic sample data</p> : <a href={`https://github.com/${dataset.repository}`} target="_blank" rel="noreferrer">View source on GitHub</a>}</div></div>
      <span className={`mode ${demo ? "demo" : "live"}`}>{demo ? "Synthetic demo" : "Live data"}</span></section>
    <div className="freshness"><span><span className="connection-dot" /> Last successful load <time data-testid="last-success" dateTime={dataset.lastSuccess}>{timestamp(dataset.lastSuccess)}</time></span>
      <span>Dataset reference <time dateTime={dataset.asOf}>{timestamp(dataset.asOf)}</time></span></div>
    {demo ? <div className="demo-note">You’re exploring a synthetic dataset fixed at {date(dataset.asOf)}. A new load updates the load time; the sample metrics stay reproducible.</div> : null}
    {data.latestRun?.status === "failed" ? <Notice title="Latest refresh failed"><p>{data.latestRun.error} Showing the last successful dataset.</p></Notice> : null}
    {data.latestRun?.status === "running" ? <div className="demo-note">Refresh in progress. Showing the last successful dataset until publication completes.</div> : null}
    {stale ? <Notice title="Dataset is more than 24 hours old"><p>Run a refresh to collect more recent repository activity.</p></Notice> : null}
    <div className="kpis"><section className="kpi"><p>Median time to merge</p><div className="metric" data-testid="merge-median">{data.metrics.medianMergeHours === null ? "—" : number(data.metrics.medianMergeHours)}<small>{data.metrics.medianMergeHours === null ? "" : "hours"}</small></div>
      <span>{data.metrics.medianMergeHours === null ? "No merged pull requests" : "From creation to merge · 12 UTC weeks"}</span></section>
      <section className="kpi"><p>Median open-issue age</p><div className="metric">{data.metrics.medianIssueDays === null ? "—" : number(data.metrics.medianIssueDays)}<small>{data.metrics.medianIssueDays === null ? "" : "days"}</small></div>
      <span>{data.metrics.medianIssueDays === null ? "No open issues" : "Since creation · Full imported history"}</span></section>
      <section className="kpi"><p>Open issues</p><div className="metric" data-testid="open-count">{data.metrics.openIssues}</div><span>True issues only · Pull requests excluded</span></section></div>
    <Charts data={data} /><Activity data={data} filters={filters} />
    <section id="methodology" className="methodology"><h2>Numbers you can explain.</h2><div><p><strong>One published snapshot.</strong> Python collects and validates every page. PostgreSQL publishes all records together, then calculates these metrics from one reference time.</p>
      <p><strong>Repeatable by design.</strong> Importing twice preserves entity keys and metrics. Failed imports keep the last successful dataset. Weeks begin Monday at 00:00 UTC; the current week is partial.</p>
      <p><strong>Useful signals, without a score.</strong> Merge time is the continuous median for PRs merged in the last 12 UTC weeks. Issue age starts at creation, including reopened issues. These metrics describe activity; they don’t grade a project.</p></div></section>
  </Frame>;
}
