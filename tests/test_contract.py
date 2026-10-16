import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from gitpulse.model import DataError, normalize
from gitpulse.github import GitHub, ImportFailure

A = datetime(2026, 1, 28, 12, tzinfo=timezone.utc)


def item(number=1, **changes):
    value = dict(
        id=100 + number,
        number=number,
        title="Fix pagination",
        state="open",
        user=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
        closed_at=None,
        html_url=f"https://github.com/example/repo/issues/{number}",
    )
    value.update(changes)
    return value


def test_issues_exclude_pull_requests_and_null_authors_are_valid():
    result = normalize([item(), item(2, pull_request={})], [], A, "example/repo")
    assert len(result) == 1
    assert result[0]["author"] is None
    assert result[0]["kind"] == "issue"


def test_closed_does_not_mean_merged():
    result = normalize(
        [],
        [
            item(
                state="closed",
                closed_at="2026-01-03T00:00:00Z",
                updated_at="2026-01-03T00:00:00Z",
                merged_at=None,
            )
        ],
        A,
        "example/repo",
    )
    assert result[0]["merged_at"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"created_at": "2030-01-01T00:00:00Z"},
        {"created_at": "2026-01-01T00:00:00"},
        {"number": -1},
        {"state": "unknown"},
        {"title": None},
        {"updated_at": "2025-01-01T00:00:00Z"},
        {"html_url": "https://evil.example/issues/1"},
    ],
)
def test_invalid_required_data_rejected(changes):
    with pytest.raises(DataError):
        normalize([item(**changes)], [], A, "example/repo")


def test_duplicate_same_version_conflicts_fail_and_newest_wins():
    assert len(normalize([item(), item()], [], A, "example/repo")) == 1
    with pytest.raises(DataError):
        normalize([item(), item(title="Conflicting")], [], A, "example/repo")
    newest = item(title="Changed", updated_at="2026-01-03T00:00:00Z")
    assert normalize([newest, item()], [], A, "example/repo")[0]["title"] == "Changed"


def test_negative_merge_duration_and_open_merged_pr_rejected():
    for changes in [
        dict(state="closed", closed_at="2026-01-02T00:00:00Z", merged_at="2025-01-01T00:00:00Z"),
        dict(merged_at="2026-01-02T00:00:00Z"),
    ]:
        with pytest.raises(DataError):
            normalize([], [item(**changes)], A, "example/repo")


def collect(handler, **options):
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await GitHub(http, "example/repo", **options).collect()

    return asyncio.run(scenario())


def handler_for(response):
    def handler(request):
        if request.url.path == "/repos/example/repo":
            return httpx.Response(
                200, json={"id": 42, "full_name": "example/repo", "private": False}
            )
        return response(request)

    return handler


def test_all_pages_and_endpoint_states_are_requested():
    def response(request):
        assert request.url.params["state"] == "all"
        if request.url.path.endswith("issues"):
            if request.url.params.get("page") == "2":
                return httpx.Response(200, json=[item(2)])
            return httpx.Response(
                200,
                json=[item()],
                headers={
                    "Link": '<https://api.github.com/repos/example/repo/issues?state=all&page=2>; rel="next"'
                },
            )
        return httpx.Response(200, json=[])

    result = collect(handler_for(response))
    assert len(result[1]) == 2


@pytest.mark.parametrize("status", [401, 403, 404, 422, 500])
def test_http_failures_never_become_empty_success(status):
    with pytest.raises(ImportFailure):
        collect(handler_for(lambda _: httpx.Response(status)), retries=0)


def test_page_cap_fails_instead_of_truncating():
    with pytest.raises(ImportFailure, match="limit"):
        collect(
            handler_for(
                lambda _: httpx.Response(
                    200,
                    json=[item()],
                    headers={
                        "Link": '<https://api.github.com/repos/example/repo/issues?page=2>; rel="next"'
                    },
                )
            ),
            max_pages=1,
        )


def test_external_pagination_url_cannot_receive_token():
    seen = []

    def response(request):
        seen.append(str(request.url))
        return httpx.Response(
            200, json=[item()], headers={"Link": '<https://evil.example/steal>; rel="next"'}
        )

    with pytest.raises(ImportFailure, match="destination"):
        collect(handler_for(response), token="not-a-real-token")
    assert all("evil.example" not in url for url in seen)


def test_rate_limit_delay_cannot_exceed_runtime_budget():
    with pytest.raises(ImportFailure, match="budget"):
        collect(
            handler_for(lambda _: httpx.Response(429, headers={"Retry-After": "1000"})), budget=2
        )


def test_transient_failure_retries_but_valid_empty_repo_succeeds():
    attempts = 0

    def response(request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(503 if attempts == 1 else 200, json=[])

    async def no_sleep(_):
        pass

    result = collect(handler_for(response), sleep=no_sleep)
    assert result[1:] == ([], [])
    assert attempts == 3
