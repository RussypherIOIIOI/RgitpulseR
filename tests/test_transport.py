import httpx
import pytest

from test_contract import collect, handler_for, item
from gitpulse.github import ImportFailure


def test_later_page_failure_never_becomes_a_complete_collection():
    def response(request):
        if request.url.params.get("page") == "2":
            return httpx.Response(503)
        return httpx.Response(
            200,
            json=[item()],
            headers={
                "Link": '<https://api.github.com/repos/example/repo/issues?page=2>; rel="next"'
            },
        )

    with pytest.raises(ImportFailure):
        collect(handler_for(response), retries=0)


def test_timeout_and_invalid_json_are_visible_failures():
    def timeout(request):
        raise httpx.ReadTimeout("sensitive request details", request=request)

    with pytest.raises(ImportFailure, match="timeout"):
        collect(handler_for(timeout), retries=0)
    with pytest.raises(ImportFailure, match="Malformed"):
        collect(handler_for(lambda _: httpx.Response(200, text="<html>unavailable</html>")))


@pytest.mark.parametrize(
    "url",
    [
        "https://api.github.com:invalid/repos/example/repo/issues",
        "https://api.github.com/repos/example/repo/issues#fragment",
    ],
)
def test_malformed_navigation_is_a_sanitized_import_failure(url):
    with pytest.raises(ImportFailure, match="destination"):
        collect(
            handler_for(
                lambda _: httpx.Response(200, json=[], headers={"Link": f'<{url}>; rel="next"'})
            )
        )


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-5"])
def test_invalid_retry_delays_fail_instead_of_retrying_early(value):
    with pytest.raises(ImportFailure, match="Invalid rate-limit"):
        collect(handler_for(lambda _: httpx.Response(429, headers={"Retry-After": value})))
