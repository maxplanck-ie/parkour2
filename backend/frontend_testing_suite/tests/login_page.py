import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    my_screen_size = {
        "width": 2560,
        "height": 1440,
    }
    return {
        **browser_context_args,
        "viewport": my_screen_size,
        "device_scale_factor": 2,
    }


def test_login_page(page: Page):
    wrongEmailId = "wrong.email.id@test.com"
    wrongPassword = "wrong.password"
    forgotPasswordEmailId = "forgot.password.email.id@ie-freiburg.mpg.de"
    correctEmailId = utilities.testEmailID
    correctPassword = utilities.testPassword

    emailInput = page.locator("input#id_username")
    passwordInput = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")
    forgotPasswordLink = page.get_by_role("link", name="Forgot password?")
    forgotPasswordEmailInput = page.get_by_label("Email address", exact=True)
    forgotPasswordEmailSubmitButton = page.get_by_role("button", name="Send reset link")

    utilities.visit_login_page(page)
    expect(page.locator("h2.form-signin-heading")).to_have_text(
        re.compile(r"Parkour LIMS\s+[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]")
    )
    forgotPasswordLink.click()
    forgotPasswordEmailInput.fill(forgotPasswordEmailId)
    forgotPasswordEmailSubmitButton.click()
    expect(page.get_by_role("heading", name="Check your email")).to_be_visible()
    expect(
        page.get_by_text(
            re.compile(r"If an active account matches the address you entered", re.I)
        )
    ).to_be_visible()
    utilities.visit_login_page(page)
    emailInput.fill(wrongEmailId)
    passwordInput.fill(wrongPassword)
    loginButton.click()
    expect(
        page.get_by_text("Your username and password didn't match. Please try again.")
    ).to_be_visible()
    emailInput.fill(correctEmailId)
    passwordInput.fill(correctPassword)
    loginButton.click()
    utilities.wait_until_authenticated(page)

    utilities.visit_vue_page(page, "libraries_and_samples")
    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )
    expect(page.get_by_role("button", name="Add Request")).to_be_visible()
