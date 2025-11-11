import datetime

import pytest
import utilities
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def test_duties_page(page: Page):
    utilities.pretest_login(page)

    host_name = utilities.get_host_name()
    page.goto(f"http://{host_name}:9980/vue/duties")
    page.bring_to_front()

    expect(page.get_by_text("Manage Duties")).to_be_visible()

    # Pick the first available options; these are always present in fixtures.
    page.locator("select#facility").select_option(index=1)
    page.locator("select#main_name").select_option(index=1)
    page.locator("select#backup_name").select_option(index=1)
    today = datetime.date.today()
    page.locator("input#start_date").fill(today.strftime("%Y-%m-%d"))
    page.locator("input#end_date").fill((today + datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
    page.locator("select#platform").select_option(index=1)
    page.locator("textarea#comment").fill("Automated UI smoke test entry")
