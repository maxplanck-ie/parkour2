import re

import pytest
import utilities
from playwright.sync_api import Page, expect


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
    forgotPasswordEmailInput = page.get_by_label("Email address:")
    forgotPasswordEmailSubmitButton = page.get_by_role(
        "button", name="Reset my password"
    )

    utilities.visit_login_page(page)
    expect(page.locator("h2.form-signin-heading")).to_have_text(
        re.compile(r"Parkour [0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]")
    )
    forgotPasswordLink.click()
    forgotPasswordEmailInput.fill(forgotPasswordEmailId)
    forgotPasswordEmailSubmitButton.click()
    expect(page.get_by_text("Password reset sent")).to_be_visible()
    expect(
        page.get_by_text("We’ve emailed you instructions for setting your password")
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
    expect(page.get_by_text("Requests").nth(0)).to_be_visible()
    expect(page.get_by_text("Libraries & Samples")).to_be_visible()
