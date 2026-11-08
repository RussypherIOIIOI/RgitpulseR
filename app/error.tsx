"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main className="status-page" id="main">
    <p className="eyebrow">GitPulse · The Meredith Collective</p>
    <h1>The dashboard could not load</h1>
    <p>Check the application connection and try again.</p>
    <button className="btn btn-primary" type="button" onClick={reset}>Try again</button>
  </main>;
}
