import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Library pk=123 ("Amplicon_1", status 1 == "Submission Completed") from
# request "18_User_Principle Investigator" ships with the fixtures -- all 20
# libraries in that request sit at status 1, which is exactly what
# IncomingLibrariesViewSet.list() filters for. Only Amplicon_1 is touched so
# the other 19 stay put and the request group doesn't disappear entirely.
REQUEST_GROUP_NAME = "18_User_Principle Investigator"
LIBRARY_NAME = "Amplicon_1"

# librariesAndSamplesView's header filters are server-side and debounce
# 2500ms before the filter is applied (see libraries_and_samples_page.py).
HEADER_FILTER_DEBOUNCE_MS = 2500
REFRESH_MARGIN_MS = 1000


def _exact(text):
    """has_text matches substrings, and "Amplicon_1" is a substring of
    "Amplicon_10".."Amplicon_19" -- require no trailing digit so it only
    matches its own row/group.
    """
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_incoming_libraries_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "incoming_libraries_samples")
    page.bring_to_front()

    utilities.expect_page_header(page, "Incoming Libraries and Samples")
    expect(page.locator(".tabulator")).to_be_visible()


def test_fail_quality_check_removes_library_from_incoming_libraries(page: Page):
    _open_incoming_libraries_page(page)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator("#tabulatorTable .tabulator-row", has_text=_exact(LIBRARY_NAME))
    if row.count() == 0:
        # Groups start collapsed (groupStartOpen: false) -- expand it.
        group_header.click()
        expect(row).to_have_count(1, timeout=15000)

    row.locator('input[type="checkbox"]').check()

    # The group's action icons are hidden until the group row is hovered
    # (".tabulator-row:hover .group-action-buttons-container"), so hover
    # before clicking -- a direct .click() leaves the button "display: none"
    # and times out.
    group_header.hover()
    group_header.locator('[title="Mark selected as Quality Checked: Failed"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(REQUEST_GROUP_NAME)
    expect(confirm_dialog).to_contain_text("Quality Check: Failed")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes -1 ("Quality Check Failed"), which drops it out of
    # IncomingLibrariesViewSet.list()'s status=1 filter -- it leaves this
    # table entirely, matching the lifecycle diagram's Incoming Libraries
    # --FAIL--> Removed branch.
    expect(row).to_have_count(0, timeout=15000)

    # The other 19 libraries in the same request are untouched.
    expect(group_header).to_have_count(1)

    # Confirm the "Removed" outcome is visible downstream too: the library
    # now shows status "Quality Check Failed" on the master Libraries and
    # Samples table.
    utilities.visit_vue_page(page, "libraries_and_samples")
    expect(page.locator(".tabulator")).to_be_visible()

    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(LIBRARY_NAME, delay=30)
    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + REFRESH_MARGIN_MS)

    failed_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(LIBRARY_NAME)
    )
    if failed_row.count() == 0:
        # Groups start collapsed here too.
        page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group",
            has_text=_exact(REQUEST_GROUP_NAME),
        ).first.click()
    expect(failed_row).to_have_count(1, timeout=15000)
    expect(failed_row.locator('[title="Quality Check Failed"]')).to_have_count(1)


def test_compromise_quality_check_removes_library_from_incoming_libraries(
    page: Page,
):
    library_name = "Amplicon_2"
    _open_incoming_libraries_page(page)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator("#tabulatorTable .tabulator-row", has_text=_exact(library_name))
    if row.count() == 0:
        # Groups start collapsed (groupStartOpen: false) -- expand it.
        group_header.click()
        expect(row).to_have_count(1, timeout=15000)

    row.locator('input[type="checkbox"]').check()

    # The group's action icons are hidden until the group row is hovered
    # (".tabulator-row:hover .group-action-buttons-container"), so hover
    # before clicking -- a direct .click() leaves the button "display: none"
    # and times out.
    group_header.hover()
    group_header.locator(
        '[title="Mark selected as Quality Checked: Compromised"]'
    ).click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(REQUEST_GROUP_NAME)
    expect(confirm_dialog).to_contain_text("Quality Check: Compromised")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes -2 ("Quality Check Compromised"), which drops it out of
    # IncomingLibrariesViewSet.list()'s status=1 filter -- it leaves this
    # table entirely, matching the lifecycle diagram's Incoming Libraries
    # --COMPROMISE--> Removed branch.
    expect(row).to_have_count(0, timeout=15000)

    # The other 19 libraries in the same request are untouched.
    expect(group_header).to_have_count(1)

    # Confirm the "Removed" outcome is visible downstream too: the library
    # now shows status "Quality Check Compromised" on the master Libraries
    # and Samples table.
    utilities.visit_vue_page(page, "libraries_and_samples")
    expect(page.locator(".tabulator")).to_be_visible()

    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(library_name, delay=30)
    page.wait_for_timeout(HEADER_FILTER_DEBOUNCE_MS + REFRESH_MARGIN_MS)

    compromised_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(library_name)
    )
    if compromised_row.count() == 0:
        # Groups start collapsed here too.
        page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group",
            has_text=_exact(REQUEST_GROUP_NAME),
        ).first.click()
    expect(compromised_row).to_have_count(1, timeout=15000)
    expect(
        compromised_row.locator('[title="Quality Check Compromised"]')
    ).to_have_count(1)


def test_incoming_libraries_samples_export_stub():
    # incoming-libraries-samples-export tracked event: deferred with the
    # other export flows (library-preparation/flowcell/run-statistics/
    # sequences-statistics/libraries-samples exports) -- no coverage yet.
    # Stub kept as a marker.
    pass
