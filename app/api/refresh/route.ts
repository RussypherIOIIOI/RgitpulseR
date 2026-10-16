import { execFile } from "node:child_process";
import path from "node:path";
import { authorizeRefresh } from "../../../lib/security";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  if (!authorizeRefresh(request, {
    enabled: process.env.GITPULSE_REFRESH_ENABLED === "true",
    token: process.env.GITPULSE_REFRESH_TOKEN ?? "",
    origin: process.env.GITPULSE_ORIGIN ?? "",
  })) return Response.json({ error: "Maintainer authorization and same-origin POST required." }, { status: 403 });

  const executable = process.env.GITPULSE_PYTHON ?? path.join(process.cwd(), ".venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
  const env: NodeJS.ProcessEnv = { NODE_ENV: process.env.NODE_ENV };
  for (const key of ["PATH", "SystemRoot", "SYSTEMROOT", "TEMP", "TMP", "HOME", "LANG",
    "DATABASE_URL", "GITPULSE_MODE", "GITPULSE_REPO", "GITHUB_TOKEN"]) {
    if (process.env[key]) env[key] = process.env[key];
  }
  const result = await new Promise<{ ok: boolean; busy: boolean }>((resolve) => {
    execFile(executable, ["-m", "gitpulse.cli", "import", "--cooldown", "60"],
      { cwd: process.cwd(), env, shell: false, timeout: 160000, maxBuffer: 8192 },
      (error) => resolve({ ok: !error, busy: error?.code === 3 }));
  });
  if (result.busy) return Response.json({ error: "Refresh already running or cooling down. Try again in one minute." }, { status: 409 });
  if (!result.ok) return Response.json({ error: "Refresh failed. Previous published data was preserved." }, { status: 503 });
  return Response.json({ message: "Refresh complete. Published data updated." });
}
