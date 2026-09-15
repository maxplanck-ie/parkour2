import re

import pytest
from playwright.sync_api import Page, expect

from . import utilities

# Samples IndexGen_Fixture_1/2 (sample.Sample pk=184/185) from request
# "27_User_IndexGen_Fixture" ship with the fixtures purpose-built for this
# test: status=2 ("Quality Check Approved"), is_pooled=False,
# index_type/index_i7/index_i5 all null, unconverted. That's exactly what
# IndexGeneratorViewSet.list()'s queryset requires (Q(is_pooled=False) &
# (Q(status=2) | Q(status=-2))) and nothing else in the shipped fixtures
# satisfies it: every other status=2 sample is already is_pooled=True
# (already sitting in a Pool), and the ones with barcode letter "L" are
# already is_converted=True, which makes the Index Generator's own
# barcode-derived "type" column read as Library rather than Sample --
# "Generate Indices" only ever applies to samples, so it would never
# enable for them.
REQUEST_GROUP_NAME = "27_User_IndexGen_Fixture"
SAMPLE_NAMES = ["IndexGen_Fixture_1", "IndexGen_Fixture_2"]
LIBRARY_PREPARATION_GROUP_NAME = "TruSeq Stranded Total RNA (Gold)"


def _exact(text):
    """has_text matches substrings -- require no trailing digit so
    "IndexGen_Fixture_1" doesn't also match a hypothetical
    "IndexGen_Fixture_10".
    """
    return re.compile(rf"{re.escape(text)}(?!\d)")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_index_generator_page(page: Page):
    utilities.pretest_login_cached(page)
    utilities.visit_vue_page(page, "index_generator")
    page.bring_to_front()

    utilities.expect_page_header(page, "Index Generator")
    expect(page.locator("#indexGeneratorSourceTable")).to_be_visible()


def _open_library_preparation_page(page: Page):
    utilities.visit_vue_page(page, "library_preparation")
    page.bring_to_front()

    utilities.expect_page_header(page, "Library Preparation")
    expect(page.locator(".tabulator")).to_be_visible()


def test_generate_indices_and_save_pool_advances_samples_to_library_preparation(
    page: Page,
):
    _open_index_generator_page(page)

    source_group = page.locator(
        "#indexGeneratorSourceTable .tabulator-row.tabulator-group",
        has_text=_exact(REQUEST_GROUP_NAME),
    )
    expect(source_group).to_have_count(1, timeout=15000)

    first_row = page.locator(
        "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(SAMPLE_NAMES[0])
    )
    if first_row.count() == 0:
        # Groups start collapsed (groupStartOpen: false) -- expand it.
        source_group.click()
        expect(first_row).to_have_count(1, timeout=15000)

    for name in SAMPLE_NAMES:
        row = page.locator(
            "#indexGeneratorSourceTable .tabulator-row", has_text=_exact(name)
        )
        expect(row).to_have_count(1, timeout=15000)
        row.locator('input[type="checkbox"]').check()

    page.locator(".add-selected-pool-button").click()

    pool_draft_table = page.locator("#indexGeneratorPoolTable")
    for name in SAMPLE_NAMES:
        expect(
            pool_draft_table.locator(".tabulator-row", has_text=_exact(name))
        ).to_have_count(1, timeout=15000)

    # These samples ship with index_type=null (see module docstring), so
    # "Generate Indices" stays disabled until an Index Type is applied.
    # "Apply to Selected Records" -> Index Type applies to every currently-
    # selected source row (the checkboxes checked above are still checked).
    # IndexType pk=46 ("Bonasio") is single-format (no extra Start
    # Coordinate control), dual-indexed, non-Nanopore, and -- unlike several
    # other single-format types shipped in the fixtures with zero actual
    # IndexI7/IndexI5 rows -- has real seeded indices (10 I7 + 10 I5), so
    # "Generate Indices" can actually produce sequences.
    index_type_select = page.locator("select.apply-index-type-select")
    expect(index_type_select).to_be_enabled()
    index_type_select.select_option(value="46")

    generate_button = page.get_by_role("button", name="Generate Indices")
    expect(generate_button).to_be_enabled()
    generate_button.click()

    # Each pool row's Index I7/I5 cells (indexGeneratorConsts.js
    # sequenceFormatter, cssClass "sequence-column sequence-text") are
    # populated once indices are generated. The chosen index type is dual
    # (is_dual=True), so both I7 and I5 fill in.
    for name in SAMPLE_NAMES:
        row = pool_draft_table.locator(".tabulator-row", has_text=_exact(name))
        sequence_cells = row.locator(".sequence-column.sequence-text")
        expect(sequence_cells).to_have_count(2)
        for i in range(2):
            expect(sequence_cells.nth(i)).not_to_have_text("", timeout=15000)

    # Color balance recomputes per cycle once real indices are assigned
    # (IndexGeneratorView.computeColorBalance): "C<n>: <red>%/<green>%" once
    # there's more than one pool row with a real index spread.
    first_cycle_balance = (
        page.locator(".balance-block").first.locator(".balance-grid span").first
    )
    expect(first_cycle_balance).to_have_text(
        re.compile(r"^C1: \d+%/\d+%$"), timeout=15000
    )

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
        pool_draft_table.locator(".tabulator-row", has_text=_exact(SAMPLE_NAMES[0]))
    ).to_have_count(0, timeout=15000)

    # Saved samples become is_pooled=True with sample.pool.name set, which
    # is exactly what LibraryPreparationViewSet.get_queryset() requires --
    # they should now appear grouped by library protocol on the Library
    # Preparation page (per pk2wiki/introduction.rst's pipeline order,
    # Index Generator comes right before Preparation).
    _open_library_preparation_page(page)

    prep_group_header = page.locator(
        "#tabulatorTable .tabulator-row.tabulator-group",
        has_text=_exact(LIBRARY_PREPARATION_GROUP_NAME),
    )
    expect(prep_group_header).to_have_count(1, timeout=15000)

    prep_row = page.locator(
        "#tabulatorTable .tabulator-row", has_text=_exact(SAMPLE_NAMES[0])
    )
    if prep_row.count() == 0:
        prep_group_header.click()
        expect(prep_row).to_have_count(1, timeout=15000)
