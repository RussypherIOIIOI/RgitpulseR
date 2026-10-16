import { dashboard } from "../../../lib/data";
import { parseFilters } from "../../../lib/filters";
export const dynamic = "force-dynamic";
export async function GET() {
  try {
    await dashboard(parseFilters({}));
    return Response.json({ status: "ready" });
  } catch {
    return Response.json({ status: "database unavailable" }, { status: 503 });
  }
}
