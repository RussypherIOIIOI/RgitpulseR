import { timingSafeEqual } from "node:crypto";

type RefreshConfig = { enabled: boolean; token: string; origin: string };

export function authorizeRefresh(request: Request, config: RefreshConfig): boolean {
  if (!config.enabled || config.token.length < 32 || !config.origin ||
      request.headers.get("origin") !== config.origin) return false;
  const provided = Buffer.from(request.headers.get("authorization") ?? "");
  const expected = Buffer.from(`Bearer ${config.token}`);
  return provided.length === expected.length && timingSafeEqual(provided, expected);
}
