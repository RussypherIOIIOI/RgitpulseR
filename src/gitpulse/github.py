"""Bounded, serial GitHub REST collection with credential-safe navigation."""

import asyncio
import math
import random
import re
import time
from urllib.parse import urlsplit

import httpx


class ImportFailure(RuntimeError):
    pass


class GitHub:
    def __init__(
        self,
        http,
        repo,
        *,
        token=None,
        retries=2,
        budget=120,
        max_pages=50,
        max_records=10000,
        sleep=asyncio.sleep,
    ):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ImportFailure("Invalid owner/repository configuration")
        self.http, self.repo = http, repo
        self.retries, self.budget = retries, budget
        self.max_pages, self.max_records = max_pages, max_records
        self.sleep = sleep
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "GitPulse-portfolio/0.1",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.started = time.monotonic()

    def remaining(self):
        remaining = self.budget - (time.monotonic() - self.started)
        if remaining <= 0:
            raise ImportFailure("Import runtime budget exhausted")
        return remaining

    def safe(self, url):
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            raise ImportFailure("Unsafe API destination") from None
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.github.com"
            or port not in (None, 443)
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise ImportFailure("Unsafe API destination")

    async def get(self, url):
        redirects = 0
        attempt = 0
        while True:
            self.safe(url)
            try:
                response = await self.http.get(
                    url,
                    headers=self.headers,
                    follow_redirects=False,
                    timeout=min(15, self.remaining()),
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self.retries:
                    raise ImportFailure("GitHub network timeout or connection failure") from exc
                response = None
            if response is not None:
                if response.status_code in (301, 302, 307, 308):
                    redirects += 1
                    if redirects > 3 or not response.headers.get("location"):
                        raise ImportFailure("Invalid API redirect")
                    url = str(response.url.join(response.headers["location"]))
                    continue
                if response.status_code == 200:
                    return response
                rate_limited = response.status_code == 429 or (
                    response.status_code == 403
                    and (
                        response.headers.get("x-ratelimit-remaining") == "0"
                        or "retry-after" in response.headers
                        or "secondary rate limit" in response.text.lower()
                    )
                )
                if not rate_limited and response.status_code not in (500, 502, 503, 504):
                    category = {
                        401: "authentication",
                        403: "forbidden",
                        404: "missing or private",
                        422: "request validation",
                    }.get(response.status_code, "unexpected HTTP")
                    raise ImportFailure(f"GitHub {category} failure ({response.status_code})")
                try:
                    for header in ("retry-after", "x-ratelimit-reset"):
                        if header in response.headers:
                            value = float(response.headers[header])
                            if not math.isfinite(value) or value < 0:
                                raise ValueError()
                    delay = (
                        max(0, float(response.headers["retry-after"]))
                        if "retry-after" in response.headers
                        else (
                            max(0, float(response.headers["x-ratelimit-reset"]) - time.time())
                            if response.headers.get("x-ratelimit-remaining") == "0"
                            else (60 * 2**attempt if rate_limited else 0.25 * 2**attempt)
                        )
                    )
                except (ValueError, KeyError):
                    raise ImportFailure("Invalid rate-limit response headers") from None
            else:
                delay = 0.25 * 2**attempt
            if delay >= self.remaining():
                raise ImportFailure("Rate-limit or retry delay exceeds remaining runtime budget")
            if attempt >= self.retries:
                raise ImportFailure("GitHub transient error: retry limit exhausted")
            await self.sleep(delay + random.random() * min(0.1, self.remaining() / 10))
            attempt += 1

    async def pages(self, endpoint):
        url = f"https://api.github.com/repos/{self.repo}/{endpoint}?state=all&sort=created&direction=asc&per_page=100"
        records, visited = [], set()
        while url:
            if url in visited or len(visited) >= self.max_pages:
                raise ImportFailure("Pagination limit or repeated page detected")
            visited.add(url)
            response = await self.get(url)
            try:
                page = response.json()
            except ValueError:
                raise ImportFailure("Malformed GitHub JSON") from None
            if not isinstance(page, list):
                raise ImportFailure("Invalid GitHub collection payload")
            records.extend(page)
            if len(records) > self.max_records:
                raise ImportFailure("Record limit exceeded")
            url = response.links.get("next", {}).get("url")
        return records

    async def collect(self):
        response = await self.get(f"https://api.github.com/repos/{self.repo}")
        try:
            repo = response.json()
            if (
                type(repo["id"]) is not int
                or repo["id"] <= 0
                or repo["private"] is not False
                or repo["full_name"].lower() != self.repo.lower()
            ):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise ImportFailure("Repository is not a valid configured public repository") from None
        issues = await self.pages("issues")
        pulls = await self.pages("pulls")
        if len(issues) + len(pulls) > self.max_records:
            raise ImportFailure("Total record limit exceeded")
        return repo, issues, pulls
