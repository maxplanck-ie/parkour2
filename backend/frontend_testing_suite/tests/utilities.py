from os import getenv as getenvvar
from platform import node as nodename
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

testEmailID = "parkour-staff@parkour-demo.ie-freiburg.mpg.de"
testPassword = "parkour-staff"


def get_host_name():
    isInsideContainer = nodename() == "parkour2-django"
    if isInsideContainer:
        hostName = "parkour2-caddy"
    else:
        hostName = getenvvar("HOSTNAME", "localhost")
    return hostName


def visit_login_page(page):
    hostName = get_host_name()
    page.goto("http://" + hostName + ":9980/login")


def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
    wait_until_authenticated(page)


def wait_until_authenticated(page: Page, *, timeout: int = 15000):
    """Wait for Django's login POST to finish and leave the login page."""
    try:
        page.wait_for_function(
            "!window.location.pathname.startsWith('/login')",
            timeout=timeout,
        )
    except PlaywrightTimeoutError as exc:
        login_error = page.get_by_text(
            "Your username and password didn't match. Please try again."
        )
        visible_error = login_error.is_visible() if login_error.count() > 0 else False
        detail = (
            " Check that the frontend fixtures are loaded."
            if visible_error
            else f" Current URL: {page.url}"
        )
        raise AssertionError(f"Login did not complete.{detail}") from exc

    hostName = get_host_name()
    page.goto(f"http://{hostName}:9980/api_user_details")
    page.wait_for_load_state("networkidle")
    if urlparse(page.url).path.startswith("/login"):
        raise AssertionError(
            "Login did not create an authenticated session. "
            "Check that the frontend fixtures are loaded."
        )
    expect(page.locator("body")).to_contain_text("USER", timeout=timeout)


def visit_vue_page(page: Page, relative_path: str):
    """Navigate to a Vue view using the authenticated session."""
    hostName = get_host_name()
    # Ensure we never end up with double slashes when callers include them.
    relative_path = relative_path.lstrip("/")
    page.goto(f"http://{hostName}:9980/vue/{relative_path}")
    page.wait_for_load_state("networkidle")
    if urlparse(page.url).path.startswith("/login"):
        raise AssertionError(
            f"Vue route /vue/{relative_path} redirected to login. "
            "Check that the login completed and frontend fixtures are loaded."
        )


def expect_page_header(
    page: Page,
    header_text: str,
    *,
    preferred_test_id: str | None = None,
    timeout: int = 15000,
):
    """Assert a page header is visible and has expected text.

    Uses data-testid when available, and falls back to a stable text-based
    selector for production bundles where explicit test IDs may be absent.
    """
    header_locator = None
    if preferred_test_id:
        by_test_id = page.get_by_test_id(preferred_test_id)
        if by_test_id.count() > 0:
            header_locator = by_test_id

    if header_locator is None:
        header_locator = page.locator(".header-title", has_text=header_text).first

    expect(header_locator).to_be_visible(timeout=timeout)
    expect(header_locator).to_have_text(header_text, timeout=timeout)
