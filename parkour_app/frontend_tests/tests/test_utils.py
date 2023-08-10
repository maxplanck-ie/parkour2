from playwright.sync_api import Page

testEmailID = "test.user@test.com"
testPassword = "StrongPassword!1"

def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    page.goto("http://127.0.0.1:9980/login")
    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
