import "server-only";
import { Pool } from "pg";
import type { Filters } from "./filters";

export type Snapshot = {
  stale: boolean;
  dataset: null | { repository: string; mode: "demo" | "live"; asOf: string;
    lastSuccess: string; runId: string; windowStart: string };
  latestRun: null | { status: "running" | "success" | "failed"; error: string | null;
    startedAt: string; finishedAt: string | null; written: number };
  metrics: { medianMergeHours: number | null; medianIssueDays: number | null;
    openIssues: number; mergedPRs: number };
  weeks: { week: string; count: number; partial: boolean }[];
  ages: number[];
  rows: { number: number; kind: "pr" | "issue"; title: string; author: string | null;
    display_state: string; created_at: string; updated_at: string; url: string }[];
  total: number; page: number;
};

const globalDb = globalThis as typeof globalThis & { gitpulsePool?: Pool };
function pool() {
  if (!process.env.DATABASE_URL) throw new Error("Database unavailable");
  if (!globalDb.gitpulsePool) {
    globalDb.gitpulsePool = new Pool({ connectionString: process.env.DATABASE_URL,
      max: 4, connectionTimeoutMillis: 5000, statement_timeout: 10000,
      options: "-c timezone=UTC" });
    globalDb.gitpulsePool.on("error", () => { console.error("GitPulse database connection interrupted"); });
  }
  return globalDb.gitpulsePool;
}

export async function dashboard(filters: Filters): Promise<Snapshot> {
  const { rows } = await pool().query<{ snapshot: Snapshot }>(
    "SELECT gitpulse_dashboard($1,$2,$3,$4,$5) AS snapshot",
    [filters.q, filters.type, filters.state, filters.page, filters.sort]);
  const data = rows[0].snapshot;
  if (data.dataset && (data.dataset.mode !== (process.env.GITPULSE_MODE ?? "demo") ||
      (data.dataset.mode === "live" && data.dataset.repository.toLowerCase() !==
       (process.env.GITPULSE_REPO ?? "").toLowerCase()))) throw new Error("Dataset configuration mismatch");
  return { ...data, stale: data.dataset?.mode === "live" &&
    Date.now() - new Date(data.dataset.asOf).getTime() > 86400000 };
}
