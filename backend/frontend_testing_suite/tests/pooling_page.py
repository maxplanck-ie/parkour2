import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Pool_16 (index_generator.Pool pk=16) ships with the fixtures: 12 libraries
# ("ATAC_1".."ATAC_12", status 2 == "Quality Check Approved", the status the
# Pooling page's own queryset requires -- see PoolingViewSet.get_queryset's
# Prefetch filter) from request "17_User_Principle Investigator", not loaded
# onto any lane. That makes it both actually visible on the Pooling page and
# safe to destroy without hitting the backend's "already loaded" guard in
# pooling.views.PoolingViewSet._return_pool_to_pooling.
POOL_NAME = "Pool_16"
REQUEST_GROUP_NAME = "17_User_Principle Investigator"
LIBRARY_NAMES = [f"ATAC_{i}" for i in range(1, 13)]


def _exact(text):
    """has_text matches substrings, and "ATAC_1" is a substring of "ATAC_10"/
    "ATAC_11"/"ATAC_12" -- require no trailing digit so each name matches
    only its own row/group.
    """
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_pooling_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "pooling")
    page.bring_to_front()

    utilities.expect_page_header(page, "Pooling")
    expect(page.locator(".tabulator")).to_be_visible()


def _open_index_generator_page(page: Page):
    utilities.visit_vue_page(page, "index_generator")
    page.bring_to_front()

    utilities.expect_page_header(page, "Index Generator")
    expect(page.locator("#indexGeneratorSourceTable")).to_be_visible()


def test_destroy_pool_and_reuse_its_records_in_a_new_pool(page: Page):
    _open_pooling_page(page)

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group", has_text=_exact(POOL_NAME)
    )
    expect(group_header).to_have_count(1, timeout=15000)

    # The group's action icons are hidden until the group row is hovered
    # (TabulatorTableFull.vue: ".tabulator-row:hover .group-action-buttons-
    # container"), so hover the row first -- a direct .click() on the
    # button alone leaves it "display: none" and times out.
    group_header.hover()
    group_header.locator('[title="Return Pool to Index Generator"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(POOL_NAME)
    confirm_dialog.locator(".popup-button.yes-button").click()

    # The pool is deleted server-side, so its group disappears entirely
    # from the Pooling table once the list refreshes.
    expect(group_header).to_have_count(0, timeout=15000)

    # The freed libraries go back to "Quality Check Approved" (status 2,
    # is_pooled False) -- exactly what the Index Generator's source table
    # queries for, so they should be selectable again immediately.
    _open_index_generator_page(page)

    source_group = page.locator(
        "#indexGeneratorSourceTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(source_group).to_have_count(1, timeout=15000)

    first_row = page.locator(
        "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(LIBRARY_NAMES[0])
    )
    if first_row.count() == 0:
        source_group.click()
        expect(first_row).to_have_count(1, timeout=15000)

    for name in LIBRARY_NAMES:
        row = page.locator(
            "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(name)
        )
        expect(row).to_have_count(1, timeout=15000)
        row.locator('input[type="checkbox"]').check()

    page.locator(".add-selected-pool-button").click()

    pool_draft_table = page.locator("#indexGeneratorPoolTable")
    for name in LIBRARY_NAMES:
        expect(
            pool_draft_table.locator(".tabulator-row", has_text=_exact(name))
        ).to_have_count(1, timeout=15000)

    # These are libraries (not samples), so they already carry indices
    # from before -- Generate Indices stays disabled (it only applies to
    # samples) and Save Pool is reachable directly once a pool size is
    # picked.
    multiplier_select = page.locator("select#index-generator-pool-multiplier")
    expect(multiplier_select).to_be_enabled()
    multiplier_select.select_option(index=1)

    size_select = page.locator("select#index-generator-pool-size")
    expect(size_select).to_be_enabled()
    size_select.select_option(index=1)

    save_button = page.locator("button.save-pool-button")
    expect(save_button).to_be_enabled()
    save_button.click()

    # Saving clears the draft pool table client-side on success.
    expect(
        pool_draft_table.locator(".tabulator-row", has_text=_exact(LIBRARY_NAMES[0]))
    ).to_have_count(0, timeout=15000)

    # A brand-new pool now owns the reused libraries. Its name is assigned
    # server-side (Pool.save() -- "Pool_<new pk>"), so rather than guess it,
    # expand every group on the Pooling page (groupStartOpen is False) and
    # look for the reused library there.
    _open_pooling_page(page)
    group_headers = page.locator("#tabulatorTable .tabulator-row.tabulator-group")
    expect(group_headers).not_to_have_count(0, timeout=15000)
    for i in range(group_headers.count()):
        group_headers.nth(i).click()

    reused_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(LIBRARY_NAMES[0])
    )
    expect(reused_row).to_have_count(1, timeout=15000)


def test_destroy_pool_reverts_converted_sample_state(page: Page):
    """Pool_17 (WGS_1..4 samples, pks 176-179, status 2, is_converted=True,
    barcode 18L0002.., loaded 0) ships with the fixtures, each with its own
    LibraryPreparation row. Returning this pool to Index Generator exercises
    pooling.views.PoolingViewSet._return_pool_to_pooling's sample-status==2
    branch: is_converted reverts to False, barcode goes back to an "S"
    prefix, and the LibraryPreparation row is deleted -- the manual, signal-
    independent inverse of library_preparation.signals.update_samples. Uses
    a separate pool from test_destroy_pool_and_reuse (Pool_16, libraries
    only) and from library_preparation_page.py (Pool_15) to avoid xdist
    cross-file interference.
    """
    _open_pooling_page(page)

    pool_name = "Pool_17"
    request_group_name = "15_User_Principle Investigator"
    sample_names = [f"WGS_{i}" for i in range(1, 5)]

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group", has_text=_exact(pool_name)
    )
    expect(group_header).to_have_count(1, timeout=15000)

    group_header.hover()
    group_header.locator('[title="Return Pool to Index Generator"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(pool_name)
    confirm_dialog.locator(".popup-button.yes-button").click()

    # Pool deleted server-side -- its group disappears from Pooling.
    expect(group_header).to_have_count(0, timeout=15000)

    # The reverted samples go back to "Quality Check Approved" (status 2,
    # is_pooled False, is_converted False) -- visible again on the Index
    # Generator source table, same as a never-pooled sample.
    _open_index_generator_page(page)

    source_group = page.locator(
        "#indexGeneratorSourceTable .tabulator-row.tabulator-group",
        has_text=_exact(request_group_name),
    )
    expect(source_group).to_have_count(1, timeout=15000)

    first_row = page.locator(
        "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(sample_names[0])
    )
    if first_row.count() == 0:
        source_group.click()
        expect(first_row).to_have_count(1, timeout=15000)

    for name in sample_names:
        row = page.locator(
            "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(name)
        )
        expect(row).to_have_count(1, timeout=15000)


def test_fail_quality_check_removes_library_from_pooling(page: Page):
    """Pool_21 (TestFail_1..5 libraries, status 2) has 5 members. Mark
    TestFail_1 as quality-check failed. Status becomes -1, which is outside
    PoolingViewSet.get_queryset()'s Prefetch filter (only {2, -2} visible),
    so TestFail_1 vanishes from its pool group. Pool group itself stays (4
    remaining members) -- matches the lifecycle Pooling --FAIL--> Removed
    branch. Uses separate pool from test_destroy_pool_and_reuse to avoid
    interference.
    """
    _open_pooling_page(page)

    pool_name = "Pool_21"
    sample_to_fail = "TestFail_1"

    group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=pool_name,
    )
    expect(group_header).to_have_count(1, timeout=15000)

    row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(sample_to_fail)
    )
    if row.count() == 0:
        # Group starts collapsed.
        group_header.click()
        expect(row).to_have_count(1, timeout=15000)

    # Click the checkbox to set selected=true on the row data.
    row.locator('input[type="checkbox"]').click()

    group_header.hover()
    group_header.locator('[title="Mark selected as Quality Checked: Failed"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(pool_name)
    expect(confirm_dialog).to_contain_text("Quality Check: Failed")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # Status becomes -1, which is outside PoolingViewSet's Prefetch filter
    # (status in {2, -2}), so TestFail_1 vanishes from its row. Group itself
    # stays because 4 other libraries remain.
    expect(row).to_have_count(0, timeout=15000)

    # Group still visible (other members untouched).
    expect(group_header).to_have_count(1)
