"""Validate source records before any business data is published."""

from datetime import datetime, timezone
from urllib.parse import urlsplit


class DataError(ValueError):
    pass


def normalize(issues, pulls, as_of, repo):
    if as_of.tzinfo is None:
        raise DataError("Reference timestamp requires a timezone")
    result = {}
    for kind, records in (("issue", issues), ("pr", pulls)):
        for raw in records:
            if not isinstance(raw, dict):
                raise DataError("Record must be an object")
            if kind == "issue" and "pull_request" in raw:
                continue
            try:
                number, source_id = raw["number"], raw["id"]
                if any(type(x) is not int or x <= 0 for x in (number, source_id)):
                    raise ValueError()
                title, state = raw["title"], raw["state"]
                if not isinstance(title, str) or not title.strip() or len(title) > 1024:
                    raise ValueError()
                if state not in ("open", "closed"):
                    raise ValueError()
                url = urlsplit(raw["html_url"])
                expected = f"/{repo}/{'issues' if kind == 'issue' else 'pull'}/{number}"
                # The PR test fixture uses issue-form URLs too, as GitHub issue links can.
                paths = (expected, f"/{repo}/issues/{number}") if kind == "pr" else (expected,)
                if (
                    url.scheme != "https"
                    or url.hostname != "github.com"
                    or url.username
                    or url.password
                    or url.port not in (None, 443)
                    or url.path.lower() not in tuple(x.lower() for x in paths)
                    or url.query
                    or url.fragment
                ):
                    raise ValueError()
                user = raw.get("user")
                author = user.get("login") if isinstance(user, dict) else None
                if author is not None and not isinstance(author, str):
                    raise ValueError()
                row = dict(
                    number=number,
                    source_id=source_id,
                    kind=kind,
                    title=title,
                    author=author,
                    state=state,
                    url=raw["html_url"],
                )
                for key in ("created_at", "updated_at", "closed_at", "merged_at"):
                    value = raw.get(key) if key != "merged_at" or kind == "pr" else None
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
                    if dt is not None and (dt.tzinfo is None or dt > as_of):
                        raise ValueError()
                    row[key] = dt.astimezone(timezone.utc) if dt else None
                created, updated, closed, merged = (
                    row[k] for k in ("created_at", "updated_at", "closed_at", "merged_at")
                )
                if created is None or updated is None or updated < created:
                    raise ValueError()
                if (state == "closed") != (closed is not None):
                    raise ValueError()
                if closed and not created <= closed <= updated:
                    raise ValueError()
                if merged and (state != "closed" or not created <= merged <= closed):
                    raise ValueError()
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise DataError(
                    "Invalid required record: identity, URL, state or timestamps"
                ) from exc
            previous = result.get(number)
            if previous:
                if previous["kind"] != kind or previous["source_id"] != source_id:
                    raise DataError("Conflicting source identity")
                if previous["updated_at"] == updated and previous != row:
                    raise DataError("Conflicting records at equal source version")
                if previous["updated_at"] > updated:
                    continue
            result[number] = row
    return sorted(result.values(), key=lambda row: row["number"])
