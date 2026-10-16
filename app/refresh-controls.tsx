"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RefreshControls({ enabled }: { enabled: boolean }) {
  const router = useRouter();
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  if (!enabled) return <span className="readonly">Read-only view</span>;
  async function refresh(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("Importing and validating the complete dataset…");
    try {
      const response = await fetch("/api/refresh", { method: "POST",
        headers: { Authorization: `Bearer ${key}` } });
      const result: { message?: string; error?: string } = await response.json();
      setMessage(result.message ?? result.error ?? "Refresh failed. Try again.");
      router.refresh();
    } catch {
      setMessage("Refresh connection lost. Reload to check the latest import status.");
    } finally { setBusy(false); }
  }
  return <details className="maintainer">
    <summary>Maintainer controls</summary>
    <form onSubmit={refresh}>
      <label htmlFor="maintainer-key">Maintainer key</label>
      <input id="maintainer-key" type="password" autoComplete="off" value={key}
        onChange={(e) => setKey(e.target.value)} required />
      <button disabled={busy} type="submit">{busy ? "Refreshing…" : "Refresh dataset"}</button>
      <p role="status" aria-live="polite">{message}</p>
    </form>
  </details>;
}
