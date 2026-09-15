import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Flowcell pk=25 ("TESTRUNSTATS1", created 2026-08-21) ships with the
# fixtures, dedicated to this file: it has one lane whose pool (Pool_22)
# holds exactly one library (StatsFixture_1, request 26) and a pre-uploaded
# "matrix" QC payload (reads_pf/cluster_pf/etc, as dissectBCL's
# fakeNews.pushParkour would send). A fixed past date range is used instead
# of the default lookback window so the test doesn't depend on "today".
FLOWCELL_ID = "TESTRUNSTATS1"
START_DATE = "2026.08.01"
END_DATE = "2026.08.31"


def _exact(text):
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_run_statistics_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "run_statistics")
    page.bring_to_front()

    utilities.expect_page_header(page, "Runs Statistics")
    expect(page.locator(".tabulator")).to_be_visible()


def test_run_statistics_shows_uploaded_matrix_data(page: Page):
    _open_run_statistics_page(page)

    page.locator("#toggleAdvancedFiltersButton").click()
    page.locator("#runsStartDate").fill(START_DATE)
    page.locator("#runsEndDate").fill(END_DATE)

    group_header = page.locator(
        "#runStatisticsTable .tabulator-row.tabulator-group",
        has_text=_exact(FLOWCELL_ID),
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator("#runStatisticsTable .tabulator-row", has_text="Pool_22")
    if row.count() == 0:
        group_header.click()
        expect(row).to_have_count(1, timeout=15000)

    # From the fixture's uploaded matrix entry: reads_pf=150000000 displays
    # in millions ("Reads PF (M)" -> "150.0"), cluster_pf=155000000 displays
    # as-is with 2 decimals, undetermined_indices=5000000 displays raw.
    expect(row).to_contain_text("150.0")
    expect(row).to_contain_text("155000000.00")
    expect(row).to_contain_text("5000000")
