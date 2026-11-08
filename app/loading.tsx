export default function Loading() {
  return <main className="status-page" aria-busy="true">
    <span className="loading-dots" aria-hidden="true"><i /><i /><i /><i /><i /></span>
    <p>Loading the published repository snapshot…</p>
  </main>;
}
