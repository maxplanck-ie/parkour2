import re
import time

from playwright.sync_api import Page, expect

correctEmailId = "dome@ie-freiburg.mpg.de"
correctPassword = "Workspace!1"

def test_login_page(page: Page):
    page.goto("http://127.0.0.1:9980/login")

    expect(page).to_have_title(re.compile("Parkour LIMS | Login"))

    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    inputEmail.fill(correctEmailId)
    inputPassword.fill(correctPassword)
    loginButton.click()
    time.sleep(2)
    page.locator("div:has-text('Parkour LIMS')")

    addButton = page.locator("a.pl-add-request-button")
    addButton.click()

    page.locator("div:has-text('New Request')")

