"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main className="loading"><h1>The dashboard could not load</h1><p>Check the application connection and try again.</p><button onClick={reset}>Try again</button></main>;
}
