import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Sample pk=175 ("Input_4", status 2 == "Quality Check Approved") from
# request "14_User_Principle Investigator" ships with the fixtures: it's
# already in Pool_15 and already has a LibraryPreparation row, which is
# exactly what LibraryPreparationViewSet.get_queryset() requires (samples
# with status in {2, -2}, sample.pool.name not null, archived=False).
# libraryPreparationView.vue groups rows by "library_protocol_name", not by
# request -- Input_4's protocol name is the group locator, while the confirm
# dialog text quotes the row's request_name instead.
GROUP_NAME = "NEBNext Ultra II DNA Library Prep Kit for Illumina"
REQUEST_NAME = "14_User_Principle Investigator"
SAMPLE_NAME = "Input_4"


def _exact(text):
    """has_text matches substrings -- require no trailing digit so a name
    like "Input_4" doesn't also match "Input_40"/"Input_41" etc.
    """
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_library_preparation_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "library_preparation")
    page.bring_to_front()

    utilities.expect_page_header(page, "Library Preparation")
    expect(page.locator(".tabulator")).to_be_visible()


def test_fail_quality_check_removes_sample_from_library_preparation(page: Page):
    _open_library_preparation_page(page)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(GROUP_NAME),
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator("#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAME))
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
    expect(confirm_dialog).to_contain_text(GROUP_NAME)
    expect(confirm_dialog).to_contain_text("Quality Check: Failed")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes -1 ("Quality Check Failed"), outside
    # LibraryPreparationViewSet's status in {2, -2} filter -- it leaves this
    # table entirely, matching the lifecycle Preparation --FAIL--> Removed
    # branch.
    expect(row).to_have_count(0, timeout=15000)

    # Confirm the "Removed" outcome is visible downstream: the sample now
    # shows status "Quality Check Failed" on the master Libraries and
    # Samples table.
    utilities.visit_vue_page(page, "libraries_and_samples")
    expect(page.locator(".tabulator")).to_be_visible()

    name_filter = page.locator(
        '.tabulator-col[tabulator-field="name"] .tabulator-header-filter input'
    )
    name_filter.click()
    name_filter.type(SAMPLE_NAME, delay=30)
    page.wait_for_timeout(3500)

    failed_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAME)
    )
    if failed_row.count() == 0:
        page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group",
            has_text=_exact(REQUEST_NAME),
        ).first.click()
    expect(failed_row).to_have_count(1, timeout=15000)
    expect(failed_row.locator('[title="Quality Check Failed"]')).to_have_count(1)


def test_library_preparation_export_stub():
    # library-preparation-export tracked event: deferred with the other
    # export flows (flowcell/run-statistics/sequences-statistics/libraries
    # -samples exports) -- no coverage yet. Stub kept as a marker.
    pass
