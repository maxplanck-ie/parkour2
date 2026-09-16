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

# LoadFlowcell_Fixture_1 (sample.Sample pk=187) from request
# "29_User_LoadFlowcell_Fixture" (request.Request pk=29), and
# LoadFlowcell_Fixture_2 (sample.Sample pk=190) from request
# "33_User_LoadFlowcell_Fixture2" (request.Request pk=33), ship with
# fixtures purpose-built for the drag-and-drop test below: status=1
# ("Submission Completed"), is_pooled=False, index_type/index_i7/index_i5
# all null. Each is the only fixture row scoped to its own request, so
# walking either through Incoming -> Index Generator -> Library
# Preparation -> Pooling -> Load Flowcells can't collide with the
# FLOWCELL_ID fixture above or any other page-object test's fixture rows.
# Two are needed because SEQUENCER_ID below has 2 lanes, and
# FlowcellSerializer requires every lane to be loaded before a flowcell
# can be saved.
REQUEST_GROUP_NAME_1 = "29_User_LoadFlowcell_Fixture"
SAMPLE_NAME_1 = "LoadFlowcell_Fixture_1"
REQUEST_GROUP_NAME_2 = "33_User_LoadFlowcell_Fixture2"
SAMPLE_NAME_2 = "LoadFlowcell_Fixture_2"

# IndexType pk=46 ("Bonasio"): single-format, dual-indexed, non-Nanopore,
# with real seeded indices (10 I7 + 10 I5) -- see index_generator_page.py's
# note that several single-format IndexType fixture rows ship with zero
# actual IndexI7/IndexI5 rows.
INDEX_TYPE_ID = "46"

LIBRARY_PREPARATION_GROUP_NAME = "TruSeq Stranded Total RNA (Gold)"

# flowcell/fixtures/sequencer.json pk=44 "AVITI 2x75 Low 100M": lanes=2,
# lane_capacity=50, active. No active single-lane Illumina/AVITI sequencer
# remains in the fixtures (flowcell/views.py's SequencerViewSet filters
# archived=False, and MiSeq pk=1 -- the previous single-lane choice here --
# was correctly marked archived after the fixtures were resynced from the
# live parkour-test snapshot). A 2-lane sequencer means both dragged pools
# are needed to fill every lane before the flowcell can be saved.
SEQUENCER_ID = "44"


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


def _mark_quality_checked_passed(page: Page, group_locator, row_locator):
    row_locator.locator('input[type="checkbox"]').check()
    group_locator.hover()
    group_locator.locator('[title="Mark selected as Quality Checked: Passed"]').click()

    confirm_dialog = page.locator(".popup-overlay")
    expect(confirm_dialog).to_be_visible()
    expect(confirm_dialog).to_contain_text("Quality Check: Passed")
    confirm_dialog.locator(".popup-button.yes-button").click()
    expect(row_locator).to_have_count(0, timeout=15000)


def _advance_sample_to_ready_pool(
    page: Page, request_group_name: str, sample_name: str
):
    """Walks the given fixture sample through Incoming -> Index Generator ->
    Library Preparation -> Pooling, mirroring
    stage_advance_chain_page.py's proven chain, and returns the resulting
    pool's name (e.g. "Pool_23"). By the time this returns, the pool is at
    status 4 and PoolListSerializer.get_ready() reports it "ready" --
    exactly what Load Flowcells' drag-and-drop needs to exercise.
    """
    # --- Incoming Libraries and Samples -- mark Quality Checked: Passed.
    _open_incoming_libraries_page(page)

    incoming_group = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(request_group_name),
    )
    expect(incoming_group).to_have_count(1, timeout=15000)

    incoming_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(sample_name)
    )
    if incoming_row.count() == 0:
        incoming_group.click()
        expect(incoming_row).to_have_count(1, timeout=15000)

    _mark_quality_checked_passed(page, incoming_group, incoming_row)

    # --- Index Generator -- select, generate indices, save pool.
    _open_index_generator_page(page)

    source_group = page.locator(
        "#indexGeneratorSourceTable .tabulator-row.tabulator-group",
        has_text=_exact(request_group_name),
    )
    expect(source_group).to_have_count(1, timeout=15000)

    source_row = page.locator(
        "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(sample_name)
    )
    if source_row.count() == 0:
        source_group.click()
        expect(source_row).to_have_count(1, timeout=15000)

    source_row.locator('input[type="checkbox"]').check()
    page.locator(".add-selected-pool-button").click()

    pool_draft_table = page.locator("#indexGeneratorPoolTable")
    expect(
        pool_draft_table.locator(".tabulator-row", has_text=_exact(sample_name))
    ).to_have_count(1, timeout=15000)

    index_type_select = page.locator("select.apply-index-type-select")
    expect(index_type_select).to_be_enabled()
    index_type_select.select_option(value=INDEX_TYPE_ID)

    generate_button = page.get_by_role("button", name="Generate Indices")
    expect(generate_button).to_be_enabled()
    generate_button.click()

    draft_row = pool_draft_table.locator(".tabulator-row", has_text=_exact(sample_name))
    sequence_cells = draft_row.locator(".sequence-column.sequence-text")
    expect(sequence_cells).to_have_count(2)
    expect(sequence_cells.first).not_to_have_text("", timeout=15000)

    # Multiplier=1 / Size=1 (index_generator.PoolSize pk=48): smallest real
    # option once sorted ascending, and small enough to fit SEQUENCER_ID's
    # lane_capacity -- the same selection stage_advance_chain_page.py
    # already proved works end to end.
    multiplier_select = page.locator("select#index-generator-pool-multiplier")
    expect(multiplier_select).to_be_enabled()
    multiplier_select.select_option(index=1)

    size_select = page.locator("select#index-generator-pool-size")
    expect(size_select).to_be_enabled()
    size_select.select_option(index=1)

    save_button = page.locator("button.save-pool-button")
    expect(save_button).to_be_enabled()
    save_button.click()

    expect(draft_row).to_have_count(0, timeout=15000)

    # --- Library Preparation -- mark Quality Checked: Passed (status 2->3).
    _open_library_preparation_page(page)

    prep_group = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(LIBRARY_PREPARATION_GROUP_NAME),
    )
    expect(prep_group).to_have_count(1, timeout=15000)

    prep_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(sample_name)
    )
    if prep_row.count() == 0:
        prep_group.click()
        expect(prep_row).to_have_count(1, timeout=15000)

    _mark_quality_checked_passed(page, prep_group, prep_row)

    # --- Pooling -- find the sample's group/pool name, then mark Quality
    # Checked: Passed (status 3->4), which is what makes the pool "ready".
    _open_pooling_page(page)

    pooling_groups = page.locator("#tabulatorTable .tabulator-row.tabulator-group")
    expect(pooling_groups).not_to_have_count(0, timeout=15000)
    for i in range(pooling_groups.count()):
        pooling_groups.nth(i).click()

    pooling_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(sample_name)
    )
    expect(pooling_row).to_have_count(1, timeout=15000)

    # Tabulator renders group headers and member rows as flat siblings
    # within the same table body (not nested), so find the enclosing group
    # via the nearest preceding ".tabulator-row.tabulator-group" sibling.
    pool_group = pooling_row.locator(
        "xpath=preceding-sibling::div"
        "[contains(concat(' ', normalize-space(@class), ' '), ' tabulator-group ')][1]"
    )
    expect(pool_group).to_have_count(1)
    pool_group_text = pool_group.inner_text()
    pool_name_match = re.search(r"Pool_\d+", pool_group_text)
    assert pool_name_match, (
        f"Could not find a 'Pool_<id>' name in pooling group text: {pool_group_text!r}"
    )
    pool_name = pool_name_match.group(0)

    _mark_quality_checked_passed(page, pool_group, pooling_row)

    return pool_name


def test_drag_ready_pool_onto_lane_and_save_flowcell(page: Page):
    pool_name_1 = _advance_sample_to_ready_pool(
        page, REQUEST_GROUP_NAME_1, SAMPLE_NAME_1
    )
    pool_name_2 = _advance_sample_to_ready_pool(
        page, REQUEST_GROUP_NAME_2, SAMPLE_NAME_2
    )

    # --- Load Flowcells -- drag each now-ready pool onto one of
    # SEQUENCER_ID's 2 lanes and save. This is the actual UI drag-and-drop
    # path, not just a readiness check (stage_advance_chain_page.py already
    # covers that a pool merely *appears* ready; here pools are placed on
    # lanes and the flowcell is created). Both lanes must be loaded --
    # FlowcellSerializer rejects a partially-loaded flowcell.
    _open_load_flowcells_page(page)

    page.locator("button.header-button", has_text="Load").click()

    load_popup = page.locator(".popup-overlay.load-flowcell-overlay")
    expect(load_popup).to_be_visible(timeout=15000)

    sequencer_select = load_popup.locator("select").first
    sequencer_select.select_option(value=SEQUENCER_ID)

    lane_cards = load_popup.locator(".lane-drop-card")
    expect(lane_cards).to_have_count(2, timeout=15000)
    expect(lane_cards.nth(0).locator(".lane-drop-card-title")).to_have_text("Lane 1")
    expect(lane_cards.nth(1).locator(".lane-drop-card-title")).to_have_text("Lane 2")

    for pool_name, lane_card in (
        (pool_name_1, lane_cards.nth(0)),
        (pool_name_2, lane_cards.nth(1)),
    ):
        pool_row = load_popup.locator(".load-pool-row", has_text=_exact(pool_name))
        expect(pool_row).to_have_count(1, timeout=15000)
        expect(pool_row).to_have_class(re.compile(r"\bready\b"))
        expect(pool_row).not_to_have_class(re.compile(r"\bdisabled\b"))

        # HTML5 drag-and-drop needs a real dispatched dragstart/drop
        # sequence -- Playwright's drag_to() handles that; a bare click
        # wouldn't trigger the component's @dragstart/@drop handlers.
        pool_row.drag_to(lane_card)

        expect(lane_card).to_have_class(re.compile(r"\bloaded\b"), timeout=15000)
        expect(lane_card.locator(".lane-drop-card-pool")).to_contain_text(pool_name)

    flowcell_id_input = load_popup.locator('input[type="text"]')
    flowcell_id_input.fill(f"E2E_{pool_name_1}")

    save_button = load_popup.locator("button.popup-button.yes-button")
    save_button.click()

    expect(load_popup).to_have_count(0, timeout=15000)

    # Saving creates a real Flowcell -- it should now appear, grouped by
    # flowcell_id, in the main Load Flowcells table.
    flowcell_group = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(f"E2E_{pool_name_1}"),
    )
    expect(flowcell_group).to_have_count(1, timeout=15000)
