from playwright.sync_api import Page

testEmailID = "test.user@test.com"
testPassword = "testing.password"

def visit_login_page(page):
    page.goto("http://127.0.0.1:9980/login")
    # page.goto("http://0.0.0.0:8000/login")

def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
