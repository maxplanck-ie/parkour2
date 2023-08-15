from os import getenv as getenvvar
from platform import node as nodename

from playwright.sync_api import Page

testEmailID = "test.user@test.com"
testPassword = "testing.password"


def visit_login_page(page):
    hostname = getenvvar("HOSTNAME", "localhost")
    if nodename() == "parkour2-django":
        # relying on docker network and extra_hosts field at compose
        page.goto("http://parkour2-caddy:9980/login")
    else:
        # assuming we're outside our docker container
        # where HOSTNAME may be defined, e.g. on the CI
        page.goto("http://" + hostname + ":9980/login")


def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
