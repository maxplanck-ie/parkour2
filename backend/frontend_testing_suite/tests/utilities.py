from os import getenv as getenvvar
from platform import node as nodename

from playwright.sync_api import Page

testEmailID = "parkour-staff@parkour-demo.ie-freiburg.mpg.de"
testPassword = "parkour-staff"


def get_host_name():
    isInsideContainer = nodename() == "parkour2-django"
    if isInsideContainer:
        hostName = "parkour2-caddy"
    else:
        hostName = getenvvar("HOSTNAME", "localhost")
    return hostName


def visit_login_page(page):
    hostName = get_host_name()
    page.goto("http://" + hostName + ":9980/login")


def pretest_login(page: Page):
    inputEmail = page.locator("input#id_username")
    inputPassword = page.locator("input#id_password")
    loginButton = page.locator("input#login_button")

    visit_login_page(page)

    inputEmail.fill(testEmailID)
    inputPassword.fill(testPassword)
    loginButton.click()
