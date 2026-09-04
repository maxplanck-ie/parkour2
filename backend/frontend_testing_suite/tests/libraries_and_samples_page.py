import pytest
from playwright.sync_api import Page, expect

from . import utilities

# librariesAndSamplesView's header filters are server-side: typing debounces
# 2500ms before the filter is applied and the table refreshes. Give that
# margin room so the assertion isn't racing the debounce timer itself.
HEADER_FILTER_DEBOUNCE_MS = 2500
REFRESH_MARGIN_MS = 1000


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Table columns use Tabulator's "fitColumns" layout, so whether the
    # table needs horizontal scroll depends on viewport width. Force a
    # narrow one so test_horizontal_scroll_survives_header_filter_refresh's
    # "Index Type requires scrolling" precondition holds regardless of the
    # default viewport (this was flaky/failing in CI at the default size).
    return {
        **browser_context_args,
        "viewport": {"width": 800, "height": 720},
    }


def _open_libraries_and_samples_page(page: Page):
    utilities.pretest_login(page)
    utilities.visit_vue_page(page, "libraries_and_samples")
    expect(page.locator(".tabulator")).to_be_visible()


def _index_type_header_filter(page: Page):
    return page.locator(
        '.tabulator-col[tabulator-field="index_type_name"] '
        ".tabulator-header-filter input"
    )


def test_header_filter_keeps_typed_value_after_debounced_refresh(page: Page):
    """Regression test for a bug where a server-side header filter (here,
    Index Type) went blank once its debounced refresh completed, even
    though the filter was still applied -- the table remounts on refresh
    (loading toggles a v-if), and the freshly (re)built Tabulator table
    isn't ready yet when the typed value gets restored onto it, so the
    restore silently no-ops and the box is left empty."""
    _open_libraries_and_samples_page(page)

    header_filter = _index_type_header_filter(page)
    header_filter.click()
    header_filter.type("Nextera", delay=30)

    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + REFRESH_MARGIN_MS)

    expect(header_filter).to_have_value("Nextera")


def test_header_filter_keeps_typed_value_after_enter(page: Page):
    """Enter should fire the search immediately (bypassing the 2500ms
    debounce) without losing the typed value either."""
    _open_libraries_and_samples_page(page)

    header_filter = _index_type_header_filter(page)
    header_filter.click()
    header_filter.type("TruSeq", delay=30)
    header_filter.press("Enter")

    page.wait_for_timeout(REFRESH_MARGIN_MS)

    expect(header_filter).to_have_value("TruSeq")


def test_header_filter_stays_focused_and_typeable_across_debounced_refresh(
    page: Page,
):
    """The debounced refresh must not steal focus or the cursor position,
    so a user who types "next", pauses, then resumes with "-era" ends up
    with "nextera" -- not a scrambled or truncated value. This was broken
    by restoreHeaderFilterValues() re-applying the filter value while the
    user was already typing again, which reset the input's cursor to the
    start."""
    _open_libraries_and_samples_page(page)

    header_filter = _index_type_header_filter(page)
    header_filter.click()
    header_filter.type("next", delay=30)

    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + REFRESH_MARGIN_MS)

    assert header_filter.evaluate("el => el === document.activeElement")

    header_filter.type("-era", delay=100)

    expect(header_filter).to_have_value("next-era")


def test_horizontal_scroll_survives_header_filter_refresh(page: Page):
    """A header-filter refresh must not reset the table's horizontal
    scroll back to the left edge while the user is scrolled into a
    right-hand column (e.g. to reach Index Type itself)."""
    _open_libraries_and_samples_page(page)

    holder = page.locator(".tabulator-tableholder").first
    header_filter = _index_type_header_filter(page)
    header_filter.click()  # scrolls the column filter into view

    scroll_left = holder.evaluate("el => el.scrollLeft")
    assert scroll_left > 0, "test setup: Index Type should require scrolling"

    header_filter.type("Nextera", delay=30)
    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + REFRESH_MARGIN_MS)

    assert holder.evaluate("el => el.scrollLeft") == scroll_left
