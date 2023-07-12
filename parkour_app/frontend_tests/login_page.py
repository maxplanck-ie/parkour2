import re
import time

from playwright.sync_api import Page, expect

correctEmailId = "test.user@test.com"
correctPassword = "StrongPassword!1"

wrongEmailId = "wrong.email.id@test.com"
wrongPassword = "WrongPassword!1"


def test_login_page(page: Page):
    page.goto("http://0.0.0.0:8000/login")

    expect(page).to_have_title(re.compile("Parkour LIMS | Login"))

    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    inputEmail.fill(wrongEmailId)
    inputPassword.fill(wrongPassword)
    loginButton.click()
    time.sleep(2)
    page.locator(
        "p:has-text('Your username and password didn't match. Please try again.')"
    )

    inputEmail.fill(correctEmailId)
    inputPassword.fill(correctPassword)
    loginButton.click()
    time.sleep(2)
    page.locator("div:has-text('Parkour LIMS')")
