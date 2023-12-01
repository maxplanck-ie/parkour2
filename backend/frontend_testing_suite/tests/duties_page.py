import csv
import os
import time
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
