from playwright.sync_api import Page, expect
import test_utils

def test_login_page(page: Page):
    wrongEmailId = "wrong.email.id@test.com"
    wrongPassword = "WrongPassword!1"
    correctEmailId = test_utils.testEmailID
    correctPassword = test_utils.testPassword
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    # page.goto("http://127.0.0.1:9980/login")
    page.goto("http://0.0.0.0:8000/login")
    expect(page.locator("h2.form-signin-heading")).to_have_text("Parkour")

    inputEmail.fill(wrongEmailId)
    inputPassword.fill(wrongPassword)
    loginButton.click()
    expect(page.get_by_text("Your username and password didn't match. Please try again.")).to_be_visible()

    inputEmail.fill(correctEmailId)
    inputPassword.fill(correctPassword)
    loginButton.click()
    expect(page.get_by_text("Requests").nth(0)).to_be_visible()
    expect(page.get_by_text("Libraries & Samples")).to_be_visible()
