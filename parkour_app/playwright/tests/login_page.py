import pytest
import utilities
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1280,
            "height": 720,
        },
    }


def test_login_page(page: Page):
    wrongEmailId = "wrong.email.id@test.com"
    wrongPassword = "wrong.password"
    correctEmailId = utilities.testEmailID
    correctPassword = utilities.testPassword
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    utilities.visit_login_page(page)
    expect(page.locator("h2.form-signin-heading")).to_have_text("Parkour")

    inputEmail.fill(wrongEmailId)
    inputPassword.fill(wrongPassword)
    loginButton.click()
    expect(
        page.get_by_text("Your username and password didn't match. Please try again.")
    ).to_be_visible()

    inputEmail.fill(correctEmailId)
    inputPassword.fill(correctPassword)
    loginButton.click()
    expect(page.get_by_text("Requests").nth(0)).to_be_visible()
    expect(page.get_by_text("Libraries & Samples")).to_be_visible()
