import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Flowcell pk=26 ("TESTSEQSTATS1", created 2026-08-22) ships with the
# fixtures, dedicated to this file: it has one lane whose pool (Pool_22)
# holds exactly one library (StatsFixture_1, barcode 26L000156, request 26)
# and a pre-uploaded "sequences" QC payload (reads_pf_sequenced/
# confident_reads, as BigRedButton's ET.sendToParkour would send). A fixed
# past date range is used instead of the default lookback window so the
# test doesn't depend on "today".
FLOWCELL_ID = "TESTSEQSTATS1"
LIBRARY_NAME = "StatsFixture_1"
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


def _open_sequences_statistics_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "sequences_statistics")
    page.bring_to_front()

    utilities.expect_page_header(page, "Sequenced Samples Statistics")
    expect(page.locator(".tabulator")).to_be_visible()


def test_sequences_statistics_shows_uploaded_sequences_data(page: Page):
    _open_sequences_statistics_page(page)

    page.locator("#toggleSequencesAdvancedFiltersButton").click()
    page.locator("#sequencesStartDate").fill(START_DATE)
    page.locator("#sequencesEndDate").fill(END_DATE)

    group_header = page.locator(
        "#sequencesStatisticsTable .tabulator-row.tabulator-group",
        has_text=_exact(FLOWCELL_ID),
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator(
        "#sequencesStatisticsTable .tabulator-row", has_text=_exact(LIBRARY_NAME)
    )
    if row.count() == 0:
        group_header.click()
        expect(row).to_have_count(1, timeout=15000)

    # reads_pf_sequenced=2000000 displays in millions ("Seq. Reads (M)");
    # confident_reads=1900000 displays as-is ("Conf. Off-species").
    expect(row).to_contain_text("2.00")
    expect(row).to_contain_text("1900000.00")


def test_sequences_statistics_export_stub():
    # sequences-statistics-export tracked event: deferred with the other
    # export flows (library-preparation/flowcell/run-statistics/libraries
    # -samples exports) -- no coverage yet. Stub kept as a marker.
    pass
