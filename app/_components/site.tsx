import Link from "next/link";
import type { ReactNode } from "react";
import { CompactMark, Icon, Lockup, type IconName } from "./brand";

export const REPOSITORY_URL = "https://github.com/RussypherIOIIOI/RgitpulseR";
const docs = (file: string) => `${REPOSITORY_URL}/blob/main/docs/${file}`;

export function SiteHeader({ status, nav = true }: { status?: string; nav?: boolean }) {
  return <header className="site-header">
    <div className="site-header-inner">
      <Link className="brand" href="/" aria-label="GitPulse home"><CompactMark size={32} /><span className="brand-name">GitPulse</span></Link>
      <span className="brand-by">by The Meredith Collective<span className="tm">™</span></span>
      {nav ? <nav className="site-nav" aria-label="Site">
        <Link href="/#overview">Dashboard</Link><Link href="/#activity">Activity</Link>
        <Link href="/#methodology">Method</Link><a href={REPOSITORY_URL}>Source</a>
      </nav> : <span className="site-nav-spacer" />}
      {status ? <span className="status-chip"><span className="status-dot" aria-hidden="true" />{status}</span> : null}
    </div>
  </header>;
}

export function SiteFooter() {
  return <footer className="site-footer">
    <div className="band-inner footer-grid">
      <div className="footer-brand"><Lockup />
        <p>GitPulse is a portfolio project from The Meredith Collective<span className="tm">™</span>:
          one repository, one published snapshot, metrics you can explain.</p></div>
      <nav className="footer-nav" aria-label="Project links">
        <a href={REPOSITORY_URL}>Source code</a><a href={docs("metrics.md")}>Metric definitions</a>
        <a href={docs("api-and-schema.md")}>API and schema</a><Link href="/#overview">Dashboard</Link>
        <Link href="/#activity">Activity</Link><Link href="/#methodology">Method</Link>
      </nav>
      <p className="fine-print">Source licensed under GPL-3.0 · Built with Python, PostgreSQL and Next.js ·
        Poppins, Lora, Space Grotesk and Matrix Sans under SIL OFL 1.1</p>
    </div>
  </footer>;
}

/** Page chrome shared by the dashboard, its recovery states and the 404 page. Recovery states
 * render without the dashboard, so they hide the in-page navigation (`nav={false}`). */
export function Frame({ children, status, nav = true }: { children: ReactNode; status?: string; nav?: boolean }) {
  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <SiteHeader status={status} nav={nav} />
    <main id="main" tabIndex={-1}>{children}</main>
    <SiteFooter />
  </>;
}

export function PatternStrip() {
  return <div className="pattern-strip" aria-hidden="true" />;
}

const principles: { icon: IconName; eyebrow: string; title: string; body: string }[] = [
  { icon: "pipeline", eyebrow: "Publication", title: "One published snapshot",
    body: "Python collects and validates every page of issues and pull requests. PostgreSQL publishes all records together, then calculates every metric from one reference time." },
  { icon: "reconcile", eyebrow: "Repeatability", title: "Imports you can run twice",
    body: "Importing twice keeps the same entity keys, and on the fixed demo clock the metrics match too. A failed import keeps the last successful dataset, so the dashboard never shows a half-written state." },
  { icon: "calendar", eyebrow: "Definitions", title: "Every window is in UTC",
    body: "Weeks begin Monday at 00:00 UTC and the current week is marked partial. Merge time is the continuous median for pull requests merged in the last 12 UTC weeks." },
  { icon: "insight", eyebrow: "Scope", title: "Signals, not a score",
    body: "Issue age starts at creation and includes reopened issues. Search and filters change the table only, so the metrics above it keep their full populations." },
];

const stack = ["Python 3.12", "httpx + asyncpg", "PostgreSQL", "Next.js 16", "React 19", "TypeScript (strict)", "pytest + Playwright", "Docker"];

/** `demo` and `readOnly` keep the stated limits true for the deployment that renders them. */
export function MethodBand({ demo, readOnly }: { demo: boolean; readOnly: boolean }) {
  return <section className="band band-light" data-theme="light" id="methodology" aria-labelledby="method-heading">
    <div className="band-inner method-grid">
      <div className="method-intro">
        <p className="eyebrow">Method</p>
        <h2 id="method-heading">Numbers you can explain</h2>
        <p className="method-lead">One repository, one published snapshot, and metrics whose definitions fit in a sentence.
          These are the controls behind every figure on this page.</p>
        <ul className="stack" aria-label="Built with">{stack.map(item => <li key={item} className="chip">{item}</li>)}</ul>
        <div className="method-links">
          <a className="btn btn-primary" href={docs("metrics.md")}>Read the metric definitions</a>
          <a className="btn" href={docs("verification.md")}>Verification</a>
        </div>
      </div>
      <div className="principles">
        {principles.map(item => <article key={item.title} className="panel principle">
          <span className="principle-icon"><Icon name={item.icon} /></span>
          <p className="eyebrow">{item.eyebrow}</p><h3>{item.title}</h3><p>{item.body}</p>
        </article>)}
        <aside className="panel principle-limits" aria-labelledby="limits-heading">
          <span className="principle-icon"><Icon name="lock" /></span>
          <div><h3 id="limits-heading">What this dashboard does not claim</h3>
            <p>{demo ? "This dataset is synthetic: the repository, authors and records are examples, and their source links are shaped like GitHub URLs without pointing to real records. "
              : "Records come from the public GitHub repository named above, as of the last successful load; newer activity appears after the next import. "}
              {readOnly ? "Visitors can’t start an import. " : "A manual refresh needs a maintainer key. "}
              The metrics describe activity. They don’t rate code quality, a project or a team.</p></div>
        </aside>
      </div>
    </div>
  </section>;
}
