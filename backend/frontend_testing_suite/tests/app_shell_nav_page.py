import pytest
from playwright.sync_api import Page, expect

from . import utilities

# The staff fixture user sees every nav entry (7 pills + the Stats dropdown),
# whose full-text width needs well over 1300px, so these two widths sit
# clearly on either side of the "labels fit" threshold.
WIDE = {"width": 2560, "height": 1440}
NARROW = {"width": 1000, "height": 800}

NAV = ".app-shell-nav:not(.app-shell-nav-measure)"
NAV_LABEL = f"{NAV} .app-shell-nav-link > span"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": WIDE}


def _open_shell(page: Page, viewport):
    utilities.pretest_login_cached(page)
    page.set_viewport_size(viewport)
    utilities.visit_vue_page(page, "libraries_and_samples")
    expect(page.locator(f"{NAV} .app-shell-nav-link").first).to_be_visible()


def _expect_expanded(page: Page):
    expect(page.locator(NAV)).not_to_have_class("app-shell-nav-collapsed")
    expect(page.locator(NAV_LABEL).first).to_be_visible()
    expect(page.locator(f"{NAV} .app-shell-nav-link[aria-label]")).to_have_count(0)


def _expect_collapsed(page: Page):
    expect(page.locator(NAV)).to_have_class("app-shell-nav app-shell-nav-collapsed")
    expect(page.locator(NAV_LABEL).first).to_be_hidden()
    # Icons stay visible and the nav never wraps into a second row.
    expect(page.locator(f"{NAV} .app-shell-nav-icon").first).to_be_visible()
    # Icon-only links keep an accessible name (and a tooltip) from their label.
    links = page.locator(f"{NAV} .app-shell-nav-link")
    for i in range(links.count()):
        link = links.nth(i)
        label = link.text_content().strip()
        expect(link).to_have_attribute("aria-label", label)
        expect(link).to_have_attribute("title", label)


def _expect_user_actions_inside_bar(page: Page):
    bar = page.locator(".app-shell-bar").bounding_box()
    logout = page.get_by_title("Logout")
    expect(logout).to_be_visible()
    box = logout.bounding_box()
    assert box["x"] + box["width"] <= bar["x"] + bar["width"]


def test_nav_shows_labels_when_there_is_room(page: Page):
    _open_shell(page, WIDE)

    _expect_expanded(page)
    _expect_user_actions_inside_bar(page)


def test_nav_collapses_to_icons_when_narrow(page: Page):
    _open_shell(page, NARROW)

    _expect_collapsed(page)
    _expect_user_actions_inside_bar(page)


def test_nav_follows_live_window_resize(page: Page):
    """Collapse state tracks the window while the page stays loaded."""
    _open_shell(page, WIDE)
    _expect_expanded(page)

    page.set_viewport_size(NARROW)
    _expect_collapsed(page)
    _expect_user_actions_inside_bar(page)

    page.set_viewport_size(WIDE)
    _expect_expanded(page)

    page.set_viewport_size(NARROW)
    _expect_collapsed(page)


def test_nav_state_is_recomputed_after_reload(page: Page):
    """A reload at a different width must not keep the previous state."""
    _open_shell(page, NARROW)
    _expect_collapsed(page)

    page.set_viewport_size(WIDE)
    page.reload()
    expect(page.locator(f"{NAV} .app-shell-nav-link").first).to_be_visible()
    _expect_expanded(page)

    page.set_viewport_size(NARROW)
    page.reload()
    expect(page.locator(f"{NAV} .app-shell-nav-link").first).to_be_visible()
    _expect_collapsed(page)
