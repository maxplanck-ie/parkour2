import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Request pk=10 ("10_User_Principle Investigator") ships with the fixtures:
# it is sequenced=True, not archived, its flowcell (pk=3) has create_time
# 2018-08-21 and isn't archived, and its 10 libraries (RNA-Seq_1..10) all sit
# in Pool_11 -- exactly what InvoicingViewSet.get_queryset() requires for a
# request to appear in a given billing month. August 2018 is a fixed,
# unchanging month so this test doesn't depend on "today".
BILLING_YEAR = "2018"
BILLING_MONTH_LABEL = "Aug"
REQUEST_NAME = "10_User_Principle Investigator"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_invoicing_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "invoicing")
    page.bring_to_front()

    utilities.expect_page_header(page, "Invoicing")
    expect(page.locator(".tabulator")).to_be_visible()


def _select_billing_month(page: Page):
    page.locator("#invoicingMonth").select_option(label=BILLING_MONTH_LABEL)
    page.locator(".month-year-picker-year").select_option(BILLING_YEAR)

    row = page.locator("#tabulatorTable .tabulator-row", has_text=REQUEST_NAME)
    expect(row).to_have_count(1, timeout=15000)
    return row


def test_invoicing_shows_billing_month_data(page: Page):
    _open_invoicing_page(page)
    row = _select_billing_month(page)
    expect(row).to_contain_text(REQUEST_NAME)


def test_export_to_excel_downloads_workbook(page: Page):
    _open_invoicing_page(page)
    _select_billing_month(page)

    page.locator("#openInvoicingExportPopupButton").click()

    export_dialog = page.locator(".export-popup")
    expect(export_dialog).to_be_visible()

    # "Export without any additional sheets" is selected by default
    # (selectedFile starts at "without-file").
    expect(page.locator("#invoicing-without-file")).to_be_checked()

    with page.expect_download() as download_info:
        export_dialog.locator(".popup-button.yes-button").click()

    download = download_info.value
    assert re.match(r"^\d{8}_invoicing\.xlsx$", download.suggested_filename)

    expect(export_dialog).to_have_count(0, timeout=15000)


def test_export_popup_reports_no_rows_for_empty_month(page: Page):
    _open_invoicing_page(page)

    # A billing month with no qualifying requests at all (long before any
    # fixture data exists).
    page.locator("#invoicingMonth").select_option(label="Jan")
    page.locator(".month-year-picker-year").select_option("2001")
    expect(page.locator("#tabulatorTable .tabulator-row")).to_have_count(
        0, timeout=15000
    )

    page.locator("#openInvoicingExportPopupButton").click()
    export_dialog = page.locator(".export-popup")
    expect(export_dialog).to_be_visible()
    export_dialog.locator(".popup-button.yes-button").click()

    expect(page.get_by_text("No invoicing rows available for export.")).to_be_visible()
