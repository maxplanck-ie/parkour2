import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Flowcell pk=6 ("e5yethethe", created 2023-07-17) ships with the fixtures:
# its one lane (pk=13) is not completed, its pool (Pool_7, 21 samples) has no
# delivered (status 6) records, and nothing else references it or its lane
# -- exactly what LoadFlowcellsView needs to show a destroyable flowcell,
# with no risk of colliding with any other test's fixture data. A fixed past
# date range is used instead of the default "this month" so the test doesn't
# depend on "today".
FLOWCELL_ID = "e5yethethe"
START_DATE = "2023.07.01"
END_DATE = "2023.07.31"


def _exact(text):
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_load_flowcells_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "load_flowcells")
    page.bring_to_front()

    utilities.expect_page_header(page, "Load Flowcells")
    expect(page.locator(".tabulator")).to_be_visible()


def _find_flowcell_group(page: Page):
    page.locator("#startDate").fill(START_DATE)
    page.locator("#endDate").fill(END_DATE)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(FLOWCELL_ID),
    )
    expect(group_header).to_have_count(1, timeout=15000)
    return group_header


def test_download_sample_sheet(page: Page):
    _open_load_flowcells_page(page)
    group_header = _find_flowcell_group(page)

    group_header.hover()
    with page.expect_download() as download_info:
        group_header.locator('[title="Download Sample Sheet"]').dispatch_event("click")

    download = download_info.value
    assert FLOWCELL_ID in download.suggested_filename


def test_destroy_flowcell_frees_its_pool(page: Page):
    _open_load_flowcells_page(page)
    group_header = _find_flowcell_group(page)

    group_header.hover()
    group_header.locator('[title="Destroy Flowcell"]').dispatch_event("click")

    confirm_dialog = page.locator(".popup-overlay", has_text="Destroy Flowcell")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(FLOWCELL_ID)
    confirm_dialog.locator(".popup-button.yes-button").click()

    expect(
        page.locator(
            "#tabulatorTable .tabulator-row.tabulator-group",
            has_text=_exact(FLOWCELL_ID),
        )
    ).to_have_count(0, timeout=15000)
