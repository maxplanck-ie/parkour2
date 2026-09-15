import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# ChainAdvance_Fixture_1 (sample.Sample pk=186) from request
# "28_User_ChainAdvance_Fixture" (request.Request pk=28) ships with the
# fixtures purpose-built for this test: status=1 ("Submission Completed"),
# is_pooled=False, index_type/index_i7/index_i5 all null, unconverted
# (barcode "26S000186", 3rd char "S"). It's the only fixture row scoped to
# this request, so marking it "Quality Checked: Passed" and walking it
# through Index Generator -> Pooling -> Load Flowcells can't collide with
# any other page-object test's fixture rows.
REQUEST_GROUP_NAME = "28_User_ChainAdvance_Fixture"
SAMPLE_NAME = "ChainAdvance_Fixture_1"

# IndexType pk=46 ("Bonasio"): single-format (no extra Start Coordinate
# control), dual-indexed, non-Nanopore, and has real seeded indices (10 I7 +
# 10 I5) -- see index_generator_page.py's note that several single-format
# IndexType fixture rows ship with zero actual IndexI7/IndexI5 rows.
INDEX_TYPE_ID = "46"

# libraryPreparationView.vue groups rows by "library_protocol_name" -- the
# fixture sample's library_protocol=11 is "TruSeq Stranded Total RNA (Gold)"
# (same group index_generator_page.py's own chain uses).
LIBRARY_PREPARATION_GROUP_NAME = "TruSeq Stranded Total RNA (Gold)"


def _exact(text):
    """has_text matches substrings -- require no trailing digit so this
    fixture's names/groups don't accidentally match some other fixture row
    sharing the same prefix.
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


def _open_index_generator_page(page: Page):
    utilities.visit_vue_page(page, "index_generator")
    page.bring_to_front()

    utilities.expect_page_header(page, "Index Generator")
    expect(page.locator("#indexGeneratorSourceTable")).to_be_visible()


def _open_library_preparation_page(page: Page):
    utilities.visit_vue_page(page, "library_preparation")
    page.bring_to_front()

    utilities.expect_page_header(page, "Library Preparation")
    expect(page.locator(".tabulator")).to_be_visible()


def _open_pooling_page(page: Page):
    utilities.visit_vue_page(page, "pooling")
    page.bring_to_front()

    utilities.expect_page_header(page, "Pooling")
    expect(page.locator(".tabulator")).to_be_visible()


def _open_load_flowcells_page(page: Page):
    utilities.visit_vue_page(page, "load_flowcells")
    page.bring_to_front()

    utilities.expect_page_header(page, "Load Flowcells")
    expect(page.locator(".tabulator")).to_be_visible()


def test_sample_advances_incoming_to_index_generator_to_pooling_to_load_flowcells(
    page: Page,
):
    # --- Stage 1: Incoming Libraries and Samples -- mark Quality Checked:
    # Passed. status 1 -> 2, which is what both IndexGeneratorViewSet's and
    # PoolingViewSet's querysets require downstream (Q(status=2)|Q(status=-2)).
    _open_incoming_libraries_page(page)

    incoming_group = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(incoming_group).to_have_count(1, timeout=15000)

    incoming_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAME)
    )
    if incoming_row.count() == 0:
        # Groups start collapsed (groupStartOpen: false) -- expand it.
        incoming_group.click()
        expect(incoming_row).to_have_count(1, timeout=15000)

    incoming_row.locator('input[type="checkbox"]').check()

    # The group's action icons are hidden until the group row is hovered.
    incoming_group.hover()
    incoming_group.locator('[title="Mark selected as Quality Checked: Passed"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text(REQUEST_GROUP_NAME)
    expect(confirm_dialog).to_contain_text("Quality Check: Passed")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes 2 ("Quality Check Approved"), outside
    # IncomingLibrariesViewSet.list()'s status=1 filter -- it leaves this
    # table.
    expect(incoming_row).to_have_count(0, timeout=15000)

    # --- Stage 2: Index Generator -- select, generate indices, save pool.
    _open_index_generator_page(page)

    source_group = page.locator(
        "#indexGeneratorSourceTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(source_group).to_have_count(1, timeout=15000)

    source_row = page.locator(
        "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(SAMPLE_NAME)
    )
    if source_row.count() == 0:
        source_group.click()
        expect(source_row).to_have_count(1, timeout=15000)

    source_row.locator('input[type="checkbox"]').check()
    page.locator(".add-selected-pool-button").click()

    pool_draft_table = page.locator("#indexGeneratorPoolTable")
    expect(
        pool_draft_table.locator(".tabulator-row", has_text=_exact(SAMPLE_NAME))
    ).to_have_count(1, timeout=15000)

    index_type_select = page.locator("select.apply-index-type-select")
    expect(index_type_select).to_be_enabled()
    index_type_select.select_option(value=INDEX_TYPE_ID)

    generate_button = page.get_by_role("button", name="Generate Indices")
    expect(generate_button).to_be_enabled()
    generate_button.click()

    draft_row = pool_draft_table.locator(".tabulator-row", has_text=_exact(SAMPLE_NAME))
    sequence_cells = draft_row.locator(".sequence-column.sequence-text")
    expect(sequence_cells).to_have_count(2)
    expect(sequence_cells.first).not_to_have_text("", timeout=15000)

    multiplier_select = page.locator("select#index-generator-pool-multiplier")
    expect(multiplier_select).to_be_enabled()
    multiplier_select.select_option(index=1)

    size_select = page.locator("select#index-generator-pool-size")
    expect(size_select).to_be_enabled()
    size_select.select_option(index=1)

    save_button = page.locator("button.save-pool-button")
    expect(save_button).to_be_enabled()
    save_button.click()

    # Saving clears the draft pool table client-side on success -- and,
    # server-side, marks the sample is_pooled=True with sample.pool set,
    # which drops it out of IndexGeneratorViewSet.list()'s
    # Q(is_pooled=False) filter.
    expect(draft_row).to_have_count(0, timeout=15000)

    # --- Stage 3: Library Preparation -- mark Quality Checked: Passed.
    # status 2 -> 3 (LibraryPreparationSerializer's BaseListSerializer.update:
    # quality_check "passed" -> sample.status = 3). This is required before
    # the sample is loadable: FlowcellViewSet.pool_list()'s samples_qs only
    # includes status__gte=3, so skipping this stage would leave the pool
    # permanently absent from Load Flowcells' Available Pools list.
    _open_library_preparation_page(page)

    prep_group = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(LIBRARY_PREPARATION_GROUP_NAME),
    )
    expect(prep_group).to_have_count(1, timeout=15000)

    prep_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAME)
    )
    if prep_row.count() == 0:
        prep_group.click()
        expect(prep_row).to_have_count(1, timeout=15000)

    prep_row.locator('input[type="checkbox"]').check()
    prep_group.hover()
    prep_group.locator('[title="Mark selected as Quality Checked: Passed"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text("Quality Check: Passed")
    confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes 3, outside LibraryPreparationViewSet's status in {2,-2}
    # filter -- it leaves this table too (same shape as the existing "Failed"
    # test, just a different terminal status).
    expect(prep_row).to_have_count(0, timeout=15000)

    # --- Stage 4: Pooling -- the new pool (name assigned server-side, e.g.
    # "Pool_<pk>") should now list the sample. Groups start collapsed, so
    # expand every group and find the one containing it.
    _open_pooling_page(page)

    pooling_groups = page.locator("#tabulatorTable .tabulator-row.tabulator-group")
    expect(pooling_groups).not_to_have_count(0, timeout=15000)
    for i in range(pooling_groups.count()):
        pooling_groups.nth(i).click()

    pooling_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAME)
    )
    expect(pooling_row).to_have_count(1, timeout=15000)

    # Tabulator renders group headers and their member rows as flat
    # siblings within the same table body (not nested), so the enclosing
    # group has to be found via the nearest preceding
    # ".tabulator-row.tabulator-group" sibling, not a descendant filter.
    pool_group = pooling_row.locator(
        "xpath=preceding-sibling::div"
        "[contains(concat(' ', normalize-space(@class), ' '), ' tabulator-group ')][1]"
    )
    expect(pool_group).to_have_count(1)
    # A group row's own text includes the pool name (e.g. "Pool_23 (...)").
    pool_group_text = pool_group.inner_text()
    pool_name_match = re.search(r"Pool_\d+", pool_group_text)
    assert pool_name_match, (
        f"Could not find a 'Pool_<id>' name in pooling group text: {pool_group_text!r}"
    )
    pool_name = pool_name_match.group(0)

    # Pooling has its own Quality Checked: Passed action (poolingConsts.js):
    # status 3 -> 4 (pooling/serializers.py's BaseListSerializer.update).
    # PoolListSerializer.get_ready() (flowcell/serializers.py) requires
    # *every* library/sample in the pool to be at status 4 before the pool
    # is "ready" to load -- so this step is required too, not just Library
    # Preparation's.
    pooling_row.locator('input[type="checkbox"]').check()
    pool_group.hover()
    pool_group.locator('[title="Mark selected as Quality Checked: Passed"]').click()

    pooling_confirm_dialog = page.locator(".popup-overlay")
    expect(pooling_confirm_dialog).to_be_visible()
    expect(pooling_confirm_dialog).to_contain_text("Quality Check: Passed")
    pooling_confirm_dialog.locator(".popup-button.yes-button").click()

    # status becomes 4, outside PoolingViewSet's status in {2, 3, -2} filter
    # -- it leaves this table too.
    expect(pooling_row).to_have_count(0, timeout=15000)

    # --- Stage 5: Load Flowcells -- the newly-saved pool (status pooled,
    # not yet loaded onto any lane) should appear as a ready-to-load
    # ("green") pool in the Load Flowcell dialog's Available Pools list.
    # This confirms the Pooling -> Load Flowcells transition without
    # performing the actual drag-and-drop lane load.
    _open_load_flowcells_page(page)

    page.locator("button.header-button", has_text="Load").click()

    load_popup = page.locator(".popup-overlay.load-flowcell-overlay")
    expect(load_popup).to_be_visible(timeout=15000)

    pool_row = load_popup.locator(".load-pool-row", has_text=_exact(pool_name))
    expect(pool_row).to_have_count(1, timeout=15000)
    expect(pool_row).to_have_class(re.compile(r"\bready\b"))
    expect(pool_row).not_to_have_class(re.compile(r"\bdisabled\b"))

    page.locator(".load-flowcell-popup .popup-close-button").click()
    expect(load_popup).to_have_count(0)
