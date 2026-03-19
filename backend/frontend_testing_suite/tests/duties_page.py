import datetime

import pytest
from playwright.sync_api import Page, expect

from . import utilities


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def test_duties_page(page: Page):
    utilities.pretest_login(page)

    utilities.visit_vue_page(page, "duties")
    page.bring_to_front()

    expect(page.get_by_text("Manage Duties")).to_be_visible()

    # Pick the first available options; these are always present in fixtures.
    page.locator("select#facility").select_option(index=1)

    main_select = page.locator("select#main_name")
    backup_select = page.locator("select#backup_name")
    expect(main_select).to_be_enabled()
    expect(backup_select).to_be_enabled()

    main_select.select_option(index=1)
    backup_select.select_option(index=1)
    today = datetime.date.today()
    page.locator("input#start_date").fill(today.strftime("%Y-%m-%d"))
    page.locator("input#end_date").fill(
        (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    )
    page.locator("select#platform").select_option(index=1)
    page.locator("textarea#comment").fill("Automated UI smoke test entry")
