import datetime
import uuid

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


def _open_duties_page(page: Page):
    utilities.pretest_login(page)

    utilities.visit_vue_page(page, "duties")
    page.bring_to_front()

    utilities.expect_page_header(
        page,
        "Manage Duties",
        preferred_test_id="duties-page-title",
    )
    expect(page.locator(".tabulator")).to_be_visible()


def _fill_add_duty_form(page: Page, comment: str, platform_index: int = 1):
    page.locator("#openAddDutyButton").click()
    expect(page.locator(".add-duty-popup")).to_be_visible()

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
    page.locator("select#platform").select_option(index=platform_index)
    page.locator("textarea#comment").fill(comment)


def test_duties_page(page: Page):
    _open_duties_page(page)
    _fill_add_duty_form(page, "Automated UI smoke test entry")


def test_add_duty_shows_row_with_capitalized_platform(page: Page):
    _open_duties_page(page)
    comment = f"Automated add-duty test {uuid.uuid4()}"

    # platform index 1 == "Short", stored server-side as "short".
    _fill_add_duty_form(page, comment, platform_index=1)
    page.locator("#saveAddDutyButton").click()

    row = page.locator("#dutiesTable .tabulator-row", has_text=comment)
    expect(row).to_have_count(1, timeout=15000)
    expect(row.locator('[tabulator-field="platform"]')).to_have_text("Short")


def test_duties_search_filters_rows(page: Page):
    _open_duties_page(page)
    comment = f"Automated search test {uuid.uuid4()}"

    _fill_add_duty_form(page, comment, platform_index=2)
    page.locator("#saveAddDutyButton").click()
    expect(page.locator("#dutiesTable .tabulator-row", has_text=comment)).to_have_count(
        1, timeout=15000
    )

    page.locator("input#search-bar").fill(comment)
    rows = page.locator("#dutiesTable .tabulator-row")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text(comment)

    page.locator("input#search-bar").fill("")
    expect(
        page.locator("#dutiesTable .tabulator-row", has_text=comment)
    ).to_be_visible()


def test_add_duty_dialog_cancel_and_escape_close_it(page: Page):
    _open_duties_page(page)

    add_button = page.locator("#openAddDutyButton")
    dialog = page.locator(".add-duty-popup")

    add_button.click()
    expect(dialog).to_be_visible()
    page.locator("#cancelAddDutyButton").click()
    expect(dialog).to_be_hidden()

    add_button.click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


def test_duties_default_filter_and_sort(page: Page):
    _open_duties_page(page)

    expect(page.locator("select#period-filter")).to_have_value("past-1-year")

    # Default sort is End Date descending (most recent first).
    end_date_header = page.locator(
        '#dutiesTable .tabulator-col[tabulator-field="end_date"]'
    )
    expect(end_date_header).to_have_attribute("aria-sort", "descending")


def test_duties_period_filter_switches_without_error(page: Page):
    _open_duties_page(page)

    page.locator("select#period-filter").select_option("all")
    expect(page.locator(".tabulator")).to_be_visible()

    page.locator("select#period-filter").select_option("upcoming")
    expect(page.locator(".tabulator")).to_be_visible()


def test_duties_inline_edit_updates_comment(page: Page):
    _open_duties_page(page)
    original_comment = f"Automated edit test {uuid.uuid4()}"
    updated_comment = f"{original_comment} edited"

    _fill_add_duty_form(page, original_comment, platform_index=1)
    page.locator("#saveAddDutyButton").click()

    page.locator("select#period-filter").select_option("all")
    row_locator = page.locator("#dutiesTable .tabulator-row", has_text=original_comment)
    expect(row_locator).to_have_count(1, timeout=15000)

    # Once editing starts, the textarea's value replaces the cell's text
    # content, so the row can no longer be re-located via has_text=original_comment;
    # grab a stable element handle for it up front instead.
    row = row_locator.element_handle()
    row.query_selector('[tabulator-field="comment"]').dblclick()

    editor = page.locator("#dutiesTable textarea")
    expect(editor).to_have_count(1, timeout=15000)
    editor.fill(updated_comment)
    # Click a non-editable cell in the same row to blur and commit the edit.
    row.query_selector('[tabulator-field="facility"]').click()

    expect(
        page.locator("#dutiesTable .tabulator-row", has_text=updated_comment)
    ).to_have_count(1, timeout=15000)
