from os import getenv as getenvvar
from platform import node as nodename

from playwright.sync_api import Page

testEmailID = "parkour-staff@parkour-demo.ie-freiburg.mpg.de"
testPassword = "parkour-staff"


def visit_login_page(page):
    inside_container = nodename() == "parkour2-django"
    if inside_container:
        my_host = "parkour2-caddy"
    else:
        my_host = getenvvar("HOSTNAME", "localhost")
    page.goto("http://" + my_host + ":9980/login")


def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
