import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# All values below are picked to be stable, non-archived fixture rows that
# actually pair together -- library_sample_shared/fixtures/analysistype.json
# pk=1 ("Other") is the only AnalysisType whose library_protocol list
# includes LibraryProtocol pk=1 ("Other - DNA Methods", not archived), which
# is what requestEditorConsts.js's filterAnalysisTypesByProtocol enforces
# in the Analysis Type dropdown once a Protocol is chosen. Organism pk=2
# ("human") is archived in the fixtures and would not appear in the
# dropdown -- pk=11 ("H. sapiens (GRCh38)") is the non-archived stand-in.
LIBRARY_PROTOCOL_TEXT = "Other - DNA Methods"
ANALYSIS_TYPE_TEXT = "Other"
ORGANISM_TEXT = "H. sapiens (GRCh38)"
READ_LENGTH_TEXT = "2x75"
# measuring_unit is a static Django choice list (library/models.py
# MEASURING_UNIT_CHOICES), not a fixture row -- "Unknown" is always valid
# and, unlike every other unit, doesn't also require a Measured Value.
MEASURING_UNIT_TEXT = "Unknown"
# IndexType pk=2 "TruSeq small RNA (I7: RPI1-RPI48)": single (not dual), not
# archived, with 48 real seeded IndexI7 rows. IndexTypeSerializer.get_index_reads
# always returns 1 for a single type and 2 for a dual one -- there is no
# IndexType with 0 reads -- so an Index I7 value is unavoidably required by
# validateLibraryRow regardless of index_type choice, even though neither
# index_i7 nor index_i5 is in LIBRARY_REQUIRED_FIELDS itself. A single type
# needs only Index I7 (not I5), which is why this one was picked over a dual
# type such as "Bonasio" (index_generator_page.py).
INDEX_TYPE_TEXT = "TruSeq small RNA"
# IndexBaseSerializer.get_name formats each option as "<index_id> - <index>"
# (e.g. IndexI7 pk=1 under IndexType pk=2: index_id "RPI1", sequence
# "ATCACG").
INDEX_I7_TEXT = "RPI1 - ATCACG"

NEW_LIBRARY_NAME = "E2ENewRequestLibrary1"
APPLY_ALL_LIBRARY_NAME_1 = "E2EApplyAllLibrary1"
APPLY_ALL_LIBRARY_NAME_2 = "E2EApplyAllLibrary2"

HEADER_FILTER_DEBOUNCE_MS = 2500


def _exact(text):
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_new_request_modal(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "libraries_and_samples")
    page.bring_to_front()

    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )

    page.get_by_test_id("add-request-button").click()
    expect(page.get_by_test_id("request-editor-title")).to_have_text("New Request")


def _row_cell(row_locator, field):
    return row_locator.locator(f'[tabulator-field="{field}"]')


def _edit_text_cell(page: Page, row_locator, field, value):
    """editor: "input" / "number" cells: dblclick opens a plain <input> inside
    the cell; type the value and commit with Enter.
    """
    cell = _row_cell(row_locator, field)
    cell.dblclick()
    input_el = cell.locator("input")
    expect(input_el).to_have_count(1, timeout=5000)
    input_el.fill(str(value))
    input_el.press("Enter")


def _edit_list_cell(page: Page, row_locator, field, option_text):
    """editor: "list" cells (Protocol, Analysis Type, Unit, Read Length,
    Organism, Index Type): dblclick focuses an <input> and opens a
    ".tabulator-edit-list" popup of ".tabulator-edit-list-item" options
    (rendered outside the cell, so located page-wide); typing filters it,
    then the matching item is clicked to commit an actual valid option
    rather than free-typed text.
    """
    cell = _row_cell(row_locator, field)
    cell.dblclick()
    input_el = cell.locator("input")
    expect(input_el).to_have_count(1, timeout=5000)
    input_el.fill(option_text)

    item = page.locator(".tabulator-edit-list-item", has_text=_exact(option_text))
    expect(item.first).to_be_visible(timeout=5000)
    item.first.click()


def _fill_required_library_fields(page: Page, row_locator, name):
    _edit_text_cell(page, row_locator, "name", name)
    # Protocol must be set before Analysis Type: the Analysis Type dropdown
    # is filtered by the currently selected Protocol.
    _edit_list_cell(page, row_locator, "library_protocol", LIBRARY_PROTOCOL_TEXT)
    _edit_list_cell(page, row_locator, "analysis_type", ANALYSIS_TYPE_TEXT)
    _edit_list_cell(page, row_locator, "measuring_unit", MEASURING_UNIT_TEXT)
    _edit_text_cell(page, row_locator, "mean_fragment_size", "300")
    _edit_text_cell(page, row_locator, "volume", "20")
    _edit_list_cell(page, row_locator, "read_length", READ_LENGTH_TEXT)
    _edit_text_cell(page, row_locator, "sequencing_depth", "30")
    _edit_list_cell(page, row_locator, "index_type", INDEX_TYPE_TEXT)
    _edit_list_cell(page, row_locator, "index_i7", INDEX_I7_TEXT)
    _edit_list_cell(page, row_locator, "organism", ORGANISM_TEXT)


def test_create_new_request_end_to_end(page: Page):
    _open_new_request_modal(page)

    description_textarea = page.get_by_test_id("request-description-input")
    description_textarea.fill("E2E full request creation coverage.")

    page.get_by_test_id("add-records-button").click()

    draft_table = page.locator("#requestEditorDraftTable")
    row = draft_table.locator(".tabulator-row").first
    expect(row).to_have_count(1, timeout=15000)

    # Toggle the Library/Sample switch with a draft row present -- this is
    # gated behind a "Switch record type?" confirm dialog (clearing the
    # draft table is destructive), exercising the request-editor-toggle-mode
    # tracked event on both open and confirm.
    record_type_slider = page.locator(".record-type-switch .slider")
    record_type_slider.click()

    toggle_confirm = page.locator(".confirm-overlay", has_text="Switch record type?")
    expect(toggle_confirm).to_be_visible()
    toggle_confirm.locator(".confirm-footer .popup-button.yes-button").click()
    expect(toggle_confirm).to_have_count(0, timeout=5000)
    expect(draft_table.locator(".tabulator-row")).to_have_count(0, timeout=5000)

    # Switch back to Library mode -- no draft rows exist yet, so this
    # applies immediately with no confirm dialog -- then re-add the row the
    # rest of the test expects.
    record_type_slider.click()
    page.get_by_test_id("add-records-button").click()
    expect(row).to_have_count(1, timeout=15000)

    _fill_required_library_fields(page, row, NEW_LIBRARY_NAME)

    save_button = page.locator(".request-editor-footer .popup-button.yes-button")
    expect(save_button).to_have_text("Save Request")

    # Tabulator's range-selection module swallows Playwright's synthetic
    # click on plain buttons inside this table-adjacent footer in the same
    # way request_editor_page.py documents for the group action icons --
    # dispatch_event bypasses that.
    with page.expect_response(
        lambda response: (
            response.url.endswith("/api/requests/")
            and response.request.method == "POST"
        )
    ) as response_info:
        save_button.dispatch_event("click")
    response = response_info.value
    assert response.ok, f"Request creation failed: {response.status}"
    body = response.json()
    assert body.get("success") is True

    # The saved library should now be visible in the main Libraries &
    # Samples table -- reload fresh to confirm it actually persisted
    # server-side rather than only existing in the draft table's local state.
    # The POST above already confirmed the request/library were persisted
    # server-side. Reload the page fresh (rather than using the modal's own
    # close button, which would otherwise raise a "Discard new request?"
    # confirmation even though the request is already saved) to verify the
    # new library is actually visible in the real table.
    utilities.visit_vue_page(page, "libraries_and_samples")
    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )
    expect(page.locator(".tabulator")).to_be_visible()

    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(NEW_LIBRARY_NAME, delay=30)
    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + 3000)

    created_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(NEW_LIBRARY_NAME)
    )
    if created_row.count() == 0:
        # Groups start collapsed (groupStartOpen: false); a fresh group for
        # a request created moments ago may not auto-expand under the
        # active search the way an existing group sometimes does.
        group_header = page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group"
        ).first
        expect(group_header).to_have_count(1, timeout=15000)
        group_header.click()
    expect(created_row).to_have_count(1, timeout=15000)


def test_apply_to_all_bulk_edit(page: Page):
    _open_new_request_modal(page)

    description_textarea = page.get_by_test_id("request-description-input")
    description_textarea.fill("E2E Apply to All coverage.")

    page.get_by_test_id("add-records-button").click()
    page.get_by_test_id("add-records-button").click()

    draft_table = page.locator("#requestEditorDraftTable")
    rows = draft_table.locator(".tabulator-row")
    expect(rows).to_have_count(2, timeout=15000)

    first_row = rows.nth(0)
    second_row = rows.nth(1)
    _edit_text_cell(page, first_row, "name", APPLY_ALL_LIBRARY_NAME_1)
    _edit_text_cell(page, second_row, "name", APPLY_ALL_LIBRARY_NAME_2)

    # Set Protocol on the first row only, then select that single cell and
    # use "Apply to All" to propagate it to every row in the table --
    # exercising the bulk-edit path rather than editing each row by hand.
    _edit_list_cell(page, first_row, "library_protocol", LIBRARY_PROTOCOL_TEXT)

    protocol_cell = _row_cell(first_row, "library_protocol")
    protocol_cell.click()

    apply_to_all_button = page.locator(
        'button.clipboard-button[title*="Apply the selected cell value"]'
    )
    expect(apply_to_all_button).to_be_enabled(timeout=5000)
    apply_to_all_button.click()

    second_row_protocol_cell = _row_cell(second_row, "library_protocol")
    expect(second_row_protocol_cell).to_contain_text(
        LIBRARY_PROTOCOL_TEXT, timeout=15000
    )

    # Select the first row and delete it -- exercises the
    # request-editor-delete-rows tracked event (confirm-dialog-gated) on
    # both open and confirm.
    _row_cell(first_row, "selected").locator('input[type="checkbox"]').check()

    delete_button = page.locator("button", has_text="Delete Selected")
    expect(delete_button).to_be_enabled(timeout=5000)
    delete_button.click()

    delete_confirm = page.locator(".confirm-overlay", has_text="permanently remove")
    expect(delete_confirm).to_be_visible()
    delete_confirm.locator(".confirm-footer .popup-button.yes-button").click()
    expect(delete_confirm).to_have_count(0, timeout=5000)
    expect(rows).to_have_count(1, timeout=15000)
