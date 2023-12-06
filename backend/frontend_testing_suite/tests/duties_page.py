import csv
import os
from datetime import datetime

import pytest
import utilities
from playwright.sync_api import Page, expect

CSV_DATA = os.path.dirname(os.path.realpath(__file__)) + "/../data/"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    my_screen_size = {
        "width": 2560,
        "height": 1440,
    }
    return {
        **browser_context_args,
        "viewport": my_screen_size,
        "device_scale_factor": 2,
    }

def test_duties_page(page: Page):
    utilities.pretest_login(page)

    hostName = utilities.get_host_name()
    dutiesButton = page.locator("a#dutiesBtn")
    manageDutiesTitle = page.get_by_text('Manage Duties')
    addFacilitySelect = page.locator("select#facility")
    addMainNameSelect = page.locator("select#main_name")
    addBackupNameSelect = page.locator("select#backup_name")
    addStartDatePicker = page.locator("input#start_date")
    addEndDatePicker = page.locator("input#end_date")
    addPlatformSelect = page.locator("select#platform")
    addCommentTextarea = page.locator("textarea#comment")
    addDutyButton = page.locator("button.save-button")
    addSuccessNotification = page.get_by_text("Duty added successfully.")
    searchBar = page.locator("input#search-bar")
    periodFilterSelect = page.locator("select#period-filter")

    dutiesButton.click()
    page.goto("http://" + hostName + ":9980/vue/duties")
    page.bring_to_front()
    expect(manageDutiesTitle).to_be_visible()
    with open(
        CSV_DATA + "duties_entries.csv",
        newline="",
        encoding="utf-8",
    ) as duties_csv_file:
        spamreader = csv.reader(duties_csv_file, delimiter=",", quotechar='"')
        for index, row in enumerate(spamreader):
            if index > 0:
                addFacilitySelect.select_option(label=row[0])
                addMainNameSelect.select_option(label=row[1])
                addBackupNameSelect.select_option(label=row[2])
                addStartDatePicker.fill(row[3])
                addEndDatePicker.fill(row[4])
                addPlatformSelect.select_option(label=row[5])
                addCommentTextarea.fill(row[6])
                addDutyButton.click()
        expect(addSuccessNotification.nth(0)).to_be_visible()