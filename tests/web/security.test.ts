import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

test("refresh requires server enablement, a valid bearer secret and exact same Origin", async () => {
  assert.ok(existsSync("lib/security.ts"), "Refresh authorization has not been implemented");
  const { authorizeRefresh } = await import("../../lib/security");
  const token = "a".repeat(40);
  const config = { enabled: true, token, origin: "http://localhost:3017" };
  const request = (origin: string, secret: string) => new Request("http://localhost:3017/api/refresh", {
    method: "POST", headers: { origin, authorization: `Bearer ${secret}` },
  });
  assert.equal(authorizeRefresh(request(config.origin, token), config), true);
  assert.equal(authorizeRefresh(request("http://evil.example", token), config), false);
  assert.equal(authorizeRefresh(request(config.origin, "wrong"), config), false);
  assert.equal(authorizeRefresh(request(config.origin, token), { ...config, enabled: false }), false);
  assert.equal(authorizeRefresh(request(config.origin, ""), { ...config, token: "" }), false);
  assert.equal(authorizeRefresh(new Request("http://localhost:3017/api/refresh", { method: "POST" }), config), false);
});

test("query bounds and sort/type/state allowlists reject malformed input", async () => {
  assert.ok(existsSync("lib/filters.ts"), "Table query validation has not been implemented");
  const { parseFilters } = await import("../../lib/filters");
  assert.deepEqual(parseFilters({ q: "  river  ", page: "2", type: "issue", state: "open", sort: "created" }),
    { q: "river", page: 2, type: "issue", state: "open", sort: "created" });
  for (const values of [{ page: "0" }, { page: "1.2" }, { page: "1e4" },
    { page: "100001" }, { type: "sql" }, { state: "deleted" }, { sort: "title;drop" }, { q: "a".repeat(201) }]) {
    assert.throws(() => parseFilters(values));
  }
});
