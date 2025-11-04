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


def _open_batch_add_modal(page: Page):
    utilities.pretest_login(page)

    add_request_button = page.locator("a.pl-add-request-button")
    description_textarea = page.locator("div.pl-description textarea")
    add_batch_button = page.locator("a.pl-batch-add-button")

    add_request_button.click()
    expect(page.get_by_text("New Request")).to_be_visible()
    description_textarea.fill("Automated UI smoke test")
    add_batch_button.click()
    expect(page.get_by_text("Add Libraries/Samples")).to_be_visible()


def _close_batch_add_modal(page: Page):
    page.locator("a.pl-close-batch-button").click()
    page.get_by_text("Close").click()


def test_requests_page(page: Page):
    _open_batch_add_modal(page)

    # Verify libraries grid allows creating empty records
    page.locator("a.pl-library-card-button").click()
    expect(page.get_by_text("Add Libraries")).to_be_visible()

    create_records_button = page.locator("a.pl-create-empty-records-button")
    create_records_button.click()
    rows = page.locator("#batch-add-grid .x-grid-row")
    expect(rows).to_have_count(1)

    # Close the batch window and the parent request window
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
