"""Run against an isolated demo server: GITPULSE_BROWSER_URL=http://localhost:3017."""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import asyncpg
from playwright.sync_api import sync_playwright, expect

pytestmark = pytest.mark.browser


def test_jarvis_theme_fonts_contrast_and_keyboard_access():
    url = os.environ.get("GITPULSE_BROWSER_URL")
    if not url:
        pytest.skip("Set GITPULSE_BROWSER_URL to the running isolated demo")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel=os.environ.get("PLAYWRIGHT_CHANNEL") or ("msedge" if os.name == "nt" else None),
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        failed_fonts = []
        page.on(
            "response",
            lambda response: (
                failed_fonts.append(response.url)
                if response.request.resource_type == "font" and not response.ok
                else None
            ),
        )
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        appearance = page.evaluate("""() => {
          const styles = s => getComputedStyle(document.querySelector(s));
          return { background: styles('body').backgroundColor,
            primary: styles('.filters button').backgroundColor,
            ready: styles('.connection-dot').backgroundColor,
            bodyFont: styles('body').fontFamily, headingFont: styles('h1').fontFamily,
            fonts: [...document.fonts].map(f => ({family: f.family, status: f.status})) };
        }""")
        assert appearance["background"] == "rgb(8, 7, 13)"
        assert appearance["primary"] == "rgb(127, 0, 255)"
        assert appearance["ready"] == "rgb(118, 185, 0)"
        assert "Matrix" in appearance["bodyFont"]
        assert "Matrix" in appearance["headingFont"]
        assert any("Matrix" in f["family"] and f["status"] == "loaded" for f in appearance["fonts"])
        assert failed_fonts == []
        chart_colors = page.evaluate("""() => {
          const style = selector => getComputedStyle(document.querySelector(selector));
          return { weeklyPlot: style('.bar-chart').backgroundColor,
            agePlot: style('.age-chart').backgroundColor,
            weeklyFill: style('.bar:not(.partial)').backgroundColor,
            weeklyAccent: style('.bar:not(.partial)').borderTopColor,
            ageFill: style('.age-track > span').backgroundColor,
            ageAccent: style('.age-track > span').backgroundImage };
        }""")
        assert chart_colors["weeklyPlot"] == chart_colors["agePlot"] == "rgb(8, 7, 13)"
        assert chart_colors["weeklyFill"] == "rgb(127, 0, 255)"
        assert chart_colors["weeklyAccent"] == "rgb(118, 185, 0)"
        assert chart_colors["ageFill"] == "rgb(118, 185, 0)"
        assert "rgb(127, 0, 255)" in chart_colors["ageAccent"]
        # Check actual computed foreground/background pairs, not just token declarations.
        pairs = page.evaluate("""() => ['.filters button','input','.state.open','.state.closed',
          '.state.merged','.readonly','th','td:nth-child(2) a','.demo-note',
          '.kpi > span','.panel-heading p','.chart-note','.bar-label','.freshness',
          '.rail-description','.filters label','.author','td time'].flatMap(selector => {
            const el = document.querySelector(selector); if (!el) return [];
            const css = getComputedStyle(el); let parent = el; let bg = css.backgroundColor;
            while ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && parent.parentElement) {
              parent = parent.parentElement; bg = getComputedStyle(parent).backgroundColor;
            }
            return [{selector, fg: css.color, bg}];
          })""")

        def luminance(color):
            channels = [
                float(v.strip()) / 255 for v in color.split("(")[1].split(")")[0].split(",")[:3]
            ]
            values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            return sum(v * w for v, w in zip(values, [0.2126, 0.7152, 0.0722]))

        for pair in pairs:
            light, dark = sorted([luminance(pair["fg"]), luminance(pair["bg"])], reverse=True)
            minimum = (
                7
                if pair["selector"]
                in {
                    ".kpi > span",
                    ".panel-heading p",
                    ".chart-note",
                    ".bar-label",
                    ".freshness",
                    ".rail-description",
                    ".filters label",
                    ".author",
                    "td time",
                }
                else 4.5
            )
            assert (light + 0.05) / (dark + 0.05) >= minimum, pair
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
        assert (
            page.get_by_role("link", name="Skip to content").evaluate(
                "el => getComputedStyle(el).outlineStyle"
            )
            != "none"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser.close()


def test_dashboard_search_pagination_and_mobile():
    url = os.environ.get("GITPULSE_BROWSER_URL")
    if not url:
        pytest.skip("Set GITPULSE_BROWSER_URL to the running isolated demo")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel=os.environ.get("PLAYWRIGHT_CHANNEL") or ("msedge" if os.name == "nt" else None),
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_role("heading", name="Repository overview")).to_be_visible()
        expect(page.get_by_text("Synthetic demo", exact=True)).to_be_visible()
        expect(page.get_by_test_id("open-count")).to_have_text("20")
        expect(page.get_by_test_id("activity-row")).to_have_count(10)
        initial = page.get_by_test_id("merge-median").inner_text()
        page.get_by_role("link", name="Next page").click()
        expect(page.get_by_text("Page 2 of 5", exact=True)).to_be_visible()
        page.get_by_label("Search activity").fill("keyboard")
        page.get_by_role("button", name="Apply filters").click()
        expect(page.get_by_test_id("activity-row")).to_have_count(3)
        expect(page.get_by_test_id("merge-median")).to_have_text(initial)
        page.get_by_role("link", name="Clear filters").click()
        expect(page.get_by_label("Search activity")).to_have_value("")
        page.get_by_label("Search activity").fill("no-such-record-xyz")
        page.get_by_role("button", name="Apply filters").click()
        expect(page.get_by_text("No activity matches these filters.")).to_be_visible()
        page.goto(url)
        Path("artifacts").mkdir(exist_ok=True)
        page.screenshot(path="artifacts/dashboard-overview.png")
        page.screenshot(path="artifacts/dashboard-desktop.png", full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path="artifacts/dashboard-mobile.png", full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert errors == []
        browser.close()


def test_manual_refresh_and_failed_attempt_preserve_last_success():
    url, token = os.environ.get("GITPULSE_BROWSER_URL"), os.environ.get("GITPULSE_REFRESH_TOKEN")
    if not url or not token or not os.environ.get("TEST_BROWSER_DATABASE_URL"):
        pytest.skip(
            "Requires isolated demo server, maintainer token and dedicated browser database"
        )
    database_url = os.environ["TEST_BROWSER_DATABASE_URL"]
    assert database_url.split("?")[0].endswith("/gitpulse_browser"), (
        "Dedicated browser database required"
    )

    def database(sql):
        async def execute():
            db = await asyncpg.connect(database_url)
            try:
                await db.execute(sql)
            finally:
                await db.close()

        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(asyncio.run, execute()).result()

    def cooldown_reset():
        database("UPDATE import_runs SET started_at=started_at-interval '61 seconds'")

    cooldown_reset()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel=os.environ.get("PLAYWRIGHT_CHANNEL") or ("msedge" if os.name == "nt" else None),
        )
        page = browser.new_page()
        page.goto(url)
        previous_success = page.get_by_test_id("last-success").get_attribute("datetime")
        page.get_by_text("Maintainer controls", exact=True).click()
        page.get_by_label("Maintainer key").fill(token)
        page.get_by_role("button", name="Refresh dataset").click()
        expect(page.get_by_role("status")).to_contain_text("Refresh complete", timeout=30000)
        expect(page.get_by_test_id("last-success")).not_to_have_attribute(
            "datetime", previous_success
        )
        success = page.get_by_test_id("last-success").get_attribute("datetime")
        # A wrong key must fail visibly without changing the publication timestamp.
        page.get_by_label("Maintainer key").fill("wrong-key")
        page.get_by_role("button", name="Refresh dataset").click()
        expect(page.get_by_role("status")).to_contain_text("authorization", timeout=10000)
        assert page.get_by_test_id("last-success").get_attribute("datetime") == success
        page.get_by_label("Maintainer key").fill(token)
        page.get_by_role("button", name="Refresh dataset").click()
        expect(page.get_by_role("status")).to_contain_text("cooling down", timeout=10000)
        assert page.get_by_test_id("last-success").get_attribute("datetime") == success
        # Exercise a real CLI persistence failure, rather than faking a browser response.
        database(
            "CREATE OR REPLACE FUNCTION browser_fail() RETURNS trigger LANGUAGE plpgsql AS $$ "
            "BEGIN RAISE EXCEPTION 'sensitive internal detail'; END $$; "
            "CREATE OR REPLACE TRIGGER browser_failure BEFORE UPDATE ON work_items "
            "FOR EACH ROW EXECUTE FUNCTION browser_fail()"
        )
        cooldown_reset()
        try:
            page.get_by_role("button", name="Refresh dataset").click()
            expect(page.get_by_role("status")).to_contain_text("Refresh failed", timeout=30000)
            expect(page.get_by_text("Latest refresh failed", exact=True)).to_be_visible()
            assert page.get_by_test_id("last-success").get_attribute("datetime") == success
            assert "sensitive internal detail" not in page.content()
        finally:
            database("ALTER TABLE work_items DISABLE TRIGGER browser_failure")
        cooldown_reset()
        page.get_by_role("button", name="Refresh dataset").click()
        expect(page.get_by_role("status")).to_contain_text("Refresh complete", timeout=30000)
        expect(page.get_by_text("Latest refresh failed", exact=True)).to_have_count(0)
        browser.close()
