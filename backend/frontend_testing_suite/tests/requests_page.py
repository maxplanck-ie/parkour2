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


def _open_batch_add_modal(page: Page):
    utilities.pretest_login(page)
    utilities.visit_vue_page(page, "libraries_and_samples")

    expect(page.get_by_test_id("libraries-header-title")).to_be_visible()

    add_request_button = page.get_by_test_id("add-request-button")
    add_request_button.click()
    expect(page.get_by_test_id("request-editor-title")).to_have_text("New Request")


def _close_batch_add_modal(page: Page):
    page.get_by_test_id("close-request-editor-button").click()
    confirm_modal = page.locator(".confirm-modal", has_text="Discard new request?")
    expect(confirm_modal).to_be_visible()
    confirm_modal.get_by_role("button", name="OK").click()
    expect(confirm_modal).not_to_be_visible()


def test_requests_page(page: Page):
    _open_batch_add_modal(page)
    description_textarea = page.get_by_test_id("request-description-input")
    description_textarea.fill("Automated UI smoke test")

    add_records_button = page.get_by_test_id("add-records-button")
    add_records_button.click()

    rows = page.locator("#requestEditorDraftTable .tabulator-row")
    expect(rows).to_have_count(1)

    _close_batch_add_modal(page)
