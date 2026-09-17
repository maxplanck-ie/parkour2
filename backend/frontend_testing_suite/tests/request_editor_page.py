import os
import re
import tempfile

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Request pk=25 ("25_User_Bioinfo") ships with the fixtures, dedicated to
# this file: it owns exactly one library (pk=155, "RequestEditorFixture_1",
# status 1) and nothing else references it, so editing its description and
# eventually deleting it can't collide with any other test's fixture data.
# Its name intentionally already matches what request.edit's save() would
# regenerate anyway (f"{id}_{user.last_name}_{user.pi.name}" for owner
# pk=3, "LIMS User" / PI "Bioinfo") -- the backend re-derives Request.name
# from the owner on every staff save regardless of what was submitted, so a
# name that didn't already match this pattern would silently change after
# the very first edit.
REQUEST_GROUP_NAME = "25_User_Bioinfo"
LIBRARY_NAME = "RequestEditorFixture_1"
UPDATED_DESCRIPTION = "Updated via Request Editor e2e test."

# librariesAndSamplesView's header filters are server-side and debounce
# 2500ms before the filter is applied (see libraries_and_samples_page.py).
HEADER_FILTER_DEBOUNCE_MS = 2500


def _exact(text):
    """has_text matches substrings -- require no trailing digit so a name
    doesn't also match a numbered sibling.
    """
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_libraries_and_samples_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "libraries_and_samples")
    page.bring_to_front()

    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )
    expect(page.locator(".tabulator")).to_be_visible()


def _find_request_group(page: Page, group_name):
    # The table has no dedicated request-name filter, and pagination can
    # push this fixture's group off the default page -- filter by the
    # library name instead, which narrows the whole table down to the one
    # request that owns it.
    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(LIBRARY_NAME, delay=30)
    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + 3000)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(group_name),
    )
    expect(group_header).to_have_count(1, timeout=15000)
    return group_header


def _open_view_edit_request(page: Page, group_name):
    group_header = _find_request_group(page, group_name)

    # Group action icons are hidden until the group row is hovered
    # (".tabulator-row:hover .group-action-buttons-container"), so hover
    # before clicking. librariesAndSamplesView's table has Tabulator's range
    # -selection module active (see its "frozen columns... selectRange"
    # console warning) -- it swallows Playwright's synthetic mousedown/
    # mouseup pair before the inline onclick ever fires, so a normal
    # .click() silently does nothing here (unlike the other views' group
    # action buttons). dispatch_event bypasses that by invoking the
    # element's "click" handler directly.
    group_header.hover()
    group_header.locator('[title="View / Edit Request"]').dispatch_event("click")

    modal = page.locator(".request-editor-modal")
    expect(modal).to_be_visible(timeout=15000)
    expect(page.get_by_test_id("request-editor-title")).to_have_text(group_name)
    return modal


def test_edit_request_description(page: Page):
    _open_libraries_and_samples_page(page)
    _open_view_edit_request(page, REQUEST_GROUP_NAME)

    description_input = page.get_by_test_id("request-description-input")
    expect(description_input).to_be_visible()
    description_input.fill(UPDATED_DESCRIPTION)

    save_button = page.locator(".request-editor-footer .popup-button.yes-button")
    expect(save_button).to_have_text("Update Request")
    save_button.dispatch_event("click")

    # A successful update closes the modal.
    expect(page.locator(".request-editor-modal")).to_have_count(0, timeout=15000)

    # Reopen to confirm the change actually persisted server-side.
    _open_libraries_and_samples_page(page)
    _open_view_edit_request(page, REQUEST_GROUP_NAME)
    expect(page.get_by_test_id("request-description-input")).to_have_value(
        UPDATED_DESCRIPTION
    )
    page.get_by_test_id("close-request-editor-button").click()


def test_upload_request_attachment(page: Page):
    _open_libraries_and_samples_page(page)
    group_header = _find_request_group(page, REQUEST_GROUP_NAME)

    group_header.hover()
    group_header.locator('[title="Attachments"]').dispatch_event("click")

    attachments_modal = page.locator(".attachments-modal")
    expect(attachments_modal).to_be_visible(timeout=15000)

    fd, file_path = tempfile.mkstemp(suffix=".txt", prefix="e2e-attachment-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("Request Editor e2e attachment upload test.")

        attachments_modal.locator('input[type="file"]').set_input_files(file_path)

        file_type_modal = page.locator(".file-type-selection-modal")
        expect(file_type_modal).to_be_visible(timeout=15000)
        file_type_row = file_type_modal.locator(".file-type-selection-row")
        # "Other" is the only option REQUEST_FILE_TYPE_OPTIONS offers, and it
        # requires a custom type name (words separated by single
        # underscores, per requestFileTypes.js's isValidRequestFileType).
        file_type_row.locator("select").select_option(label="Other")
        file_type_row.locator("input").fill("E2E_Attachment")

        save_button = file_type_modal.locator(".popup-footer .popup-button.yes-button")
        expect(save_button).to_be_enabled(timeout=5000)
        save_button.click()

        expect(file_type_modal).to_have_count(0, timeout=15000)
        expect(
            attachments_modal.locator(
                ".file-name-text", has_text=os.path.basename(file_path)
            )
        ).to_have_count(1, timeout=15000)
    finally:
        os.remove(file_path)

    attachments_modal.locator(".popup-footer .popup-button.yes-button").click()
    expect(attachments_modal).to_have_count(0, timeout=15000)


def test_upload_signed_request_stub():
    # request-upload-signed tracked event has no reachable UI trigger:
    # canUploadSignedRequest/canDownloadRequestForm are computed in
    # librariesAndSamplesView.vue but librariesAndSamplesGroupHeader() never
    # renders a button for them (dead code, no click path exists). Stub
    # kept as a marker until that's fixed or the tracking is removed.
    pass


def test_compose_email_stub():
    # request-compose-email's Send button posts to a real SMTP EMAIL_HOST
    # (backend/config/settings/base.py) with no confirmed test-safe backend
    # in the playwright/CI environment -- driving it here risks an actual
    # send or a hang on connect. Needs an EMAIL_BACKEND stub before this
    # can be a real test.
    pass


def test_solicit_approval_stub():
    # request-solicit-approval shares compose-email's real-SMTP risk above,
    # and is additionally gated behind a paperlessApproval user flag whose
    # fixture truthiness is unverified. Needs both resolved before this can
    # be a real test.
    pass


def test_request_editor_file_type_selection_stub():
    # request-editor-file-type-selection: the request editor's own upload
    # zone (requestEditorView.vue, distinct from the Attachments popup
    # covered by test_upload_request_attachment above) -- locator/flow not
    # yet mapped out. Stub kept as a marker for follow-up.
    pass


def test_request_editor_delete_file_stub():
    # request-editor-delete-file: same requestEditorView.vue upload zone as
    # above, delete-uploaded-file path -- locator/flow not yet mapped out.
    # Stub kept as a marker for follow-up.
    pass


def test_table_paste_errors_stub():
    # table-paste-errors (TabulatorTableFull.vue:695): needs Playwright
    # clipboard-paste emulation into a Tabulator cell to trigger invalid-
    # paste handling -- not yet investigated for feasibility. Stub kept as
    # a marker for follow-up.
    pass


def test_delete_request(page: Page):
    _open_libraries_and_samples_page(page)

    group_header = _find_request_group(page, REQUEST_GROUP_NAME)
    group_header.hover()
    group_header.locator('[title="Delete Request"]').dispatch_event("click")

    confirm_dialog = page.locator(".popup-overlay", has_text="Delete Request")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(REQUEST_GROUP_NAME)
    confirm_dialog.locator(".popup-button.yes-button").click()

    expect(confirm_dialog).to_have_count(0, timeout=15000)

    # The request (and its one library) is gone from the master table.
    expect(
        page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group",
            has_text=_exact(REQUEST_GROUP_NAME),
        )
    ).to_have_count(0, timeout=15000)

    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(LIBRARY_NAME, delay=30)
    page.wait_for_timeout(3500)
    expect(
        page.locator("#tabulatorTable .tabulator-row", has_text=_exact(LIBRARY_NAME))
    ).to_have_count(0, timeout=15000)
