export type Filters = { q: string; type: string; state: string; page: number; sort: string };
export function parseFilters(input: Record<string, string | string[] | undefined>): Filters {
  const value = (key: string, fallback = "") => {
    const v = input[key];
    if (Array.isArray(v)) throw new Error("Duplicate query parameter");
    return v ?? fallback;
  };
  const q = value("q").trim(), type = value("type"), state = value("state");
  const sort = value("sort", "updated"), rawPage = value("page", "1");
  if (q.length > 200 || !["", "issue", "pr"].includes(type) ||
      !["", "open", "closed", "merged"].includes(state) ||
      !["updated", "created"].includes(sort) || !/^[1-9]\d{0,5}$/.test(rawPage) ||
      Number(rawPage) > 100000) throw new Error("Invalid table filters");
  return { q, type, state, sort, page: Number(rawPage) };
}
