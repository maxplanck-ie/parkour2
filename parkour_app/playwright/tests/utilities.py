from playwright.sync_api import Page

testEmailID = "test.user@test.com"
testPassword = "testing.password"


def visit_login_page(page):
    page.goto("http://parkour2-caddy:9980/login")


def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
