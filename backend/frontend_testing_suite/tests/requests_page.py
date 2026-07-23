from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, expect

from . import utilities


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 2560, "height": 1440},
        "device_scale_factor": 2,
    }


def _open_batch_add_modal(page: Page):
    utilities.pretest_login(page)
    utilities.visit_vue_page(page, "libraries_and_samples")

    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )

    add_request_button = page.get_by_test_id("add-request-button")
    add_request_button.click()
    expect(page.get_by_test_id("request-editor-title")).to_have_text("New Request")


def _close_batch_add_modal(page: Page):
    page.get_by_test_id("close-request-editor-button").click()
    confirm_modal = page.locator(".confirm-modal", has_text="Discard new request?")
    expect(confirm_modal).to_be_visible()
    confirm_modal.get_by_role("button", name="OK").click()
    expect(confirm_modal).not_to_be_visible()


def _mock_libraries_and_samples_for_ro_crate(page: Page, status=6):
    page.route(
        "**/api_user_details",
        lambda route: route.fulfill(
            json={
                "USER": {
                    "id": 1,
                    "is_staff": True,
                    "paperless_approval": False,
                }
            }
        ),
    )
    page.route(
        "**/api/libraries-and-samples-templates/**",
        lambda route: route.fulfill(json=[]),
    )
    page.route(
        "**/api/libraries_and_samples/**",
        lambda route: route.fulfill(
            json={
                "page_size": 10,
                "total_pages": 1,
                "total": 1,
                "requests": {
                    "101": {
                        "id": 101,
                        "name": "101_ROCrate Request",
                        "restrict_permissions": False,
                    }
                },
                "children": [
                    {
                        "pk": 501,
                        "record_type": "library",
                        "request_id": 101,
                        "request_name": "101_ROCrate Request",
                        "name": "RO-Crate library",
                        "barcode": "26L000501",
                        "status": status,
                        "library_protocol_name": "RNA Library",
                        "analysis_type_name": "RNA-seq",
                        "read_length_name": "2x150",
                        "organism_name": "Arabidopsis",
                        "measured_value": 10,
                        "measuring_unit": "ng",
                        "measured_value_facility": 10,
                        "measuring_unit_facility": "ng",
                        "pool_names": [],
                        "flowcell_ids": [],
                        "sequencer_ids": [],
                        "sequencer_names": [],
                    }
                ],
            }
        ),
    )


def _open_libraries_page_with_ro_crate_data(page: Page, status=6):
    utilities.pretest_login(page)
    _mock_libraries_and_samples_for_ro_crate(page, status=status)
    utilities.visit_vue_page(page, "libraries_and_samples")
    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )
    expect(page.get_by_text("101_ROCrate Request").first).to_be_visible()


def _select_first_ro_crate_row(page: Page):
    if page.locator("#tabulatorTable input[type='checkbox']").count() == 0:
        page.locator("#tabulatorTable .tabulator-group").first.click()
    page.locator("#tabulatorTable input[type='checkbox']").first.check(force=True)
    page.get_by_test_id("open-ro-crate-preview-button").click()
    expect(page.get_by_test_id("ro-crate-preview-overlay")).to_be_visible()


def _ro_crate_preview_payload():
    return {
        "archive_name": "101_102_ro_crate.zip",
        "skipped_records": [],
        "ro_crate": {
            "@context": ["https://w3id.org/ro/crate/1.1/context"],
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Parkour RO-Crate export (2 requests)",
                    "hasPart": [
                        {"@id": "#request-context-101"},
                        {"@id": "#request-context-102"},
                        {"@id": "#study-101"},
                        {"@id": "#study-102"},
                    ],
                },
                {
                    "@id": "#request-context-101",
                    "@type": "Dataset",
                    "name": "101_ROCrate Request",
                    "description": "Preview request description",
                    "additionalProperty": [
                        {"@id": "#request-101-name"},
                        {"@id": "#request-101-qc-completed-at"},
                    ],
                },
                {
                    "@id": "#request-101-name",
                    "@type": "PropertyValue",
                    "name": "request_name",
                    "value": "101_ROCrate Request",
                },
                {
                    "@id": "#request-101-qc-completed-at",
                    "@type": "PropertyValue",
                    "name": "request_qc_completed_at",
                    "value": "2026-04-02T12:00:00Z",
                },
                {
                    "@id": "#study-101",
                    "@type": "Dataset",
                    "name": "Study for 101_ROCrate Request",
                    "materials": {"otherMaterials": [{"@id": "#library-material-501"}]},
                    "assays": [{"@id": "#library-assay-501"}],
                    "processSequence": [{"@id": "#library-process-501"}],
                    "dataFiles": [{"@id": "#library-data-501"}],
                },
                {
                    "@id": "#library-material-501",
                    "@type": "Thing",
                    "name": "Delivered library",
                    "identifier": "26L000501",
                    "additionalType": {"@id": "https://w3id.org/isa/Library"},
                    "organism": {"@id": "#organism-1"},
                    "additionalProperty": [
                        {"@id": "#library-501-name"},
                        {"@id": "#library-501-analysis"},
                        {"@id": "#library-501-status"},
                        {"@id": "#library-501-organism"},
                        {"@id": "#library-501-read-length"},
                        {"@id": "#library-501-depth"},
                        {"@id": "#library-501-flowcells"},
                        {"@id": "#library-501-sequencers"},
                        {"@id": "#library-501-input-value"},
                        {"@id": "#library-501-input-unit"},
                        {"@id": "#library-501-concentration"},
                        {"@id": "#library-501-create-time"},
                    ],
                },
                {
                    "@id": "#library-501-name",
                    "@type": "PropertyValue",
                    "name": "library_db_name",
                    "value": "Delivered library",
                },
                {
                    "@id": "#library-501-analysis",
                    "@type": "PropertyValue",
                    "name": "library_mv_analysis_type_name",
                    "value": "RNA-seq",
                },
                {
                    "@id": "#library-501-status",
                    "@type": "PropertyValue",
                    "name": "library_mv_status",
                    "value": 6,
                },
                {
                    "@id": "#library-501-organism",
                    "@type": "PropertyValue",
                    "name": "library_mv_organism_name",
                    "value": "Arabidopsis",
                },
                {
                    "@id": "#library-501-read-length",
                    "@type": "PropertyValue",
                    "name": "library_mv_read_length_name",
                    "value": "2x150",
                },
                {
                    "@id": "#library-501-depth",
                    "@type": "PropertyValue",
                    "name": "library_mv_sequencing_depth",
                    "value": 25,
                },
                {
                    "@id": "#library-501-flowcells",
                    "@type": "PropertyValue",
                    "name": "library_mv_flowcell_ids",
                    "value": ["FC001"],
                },
                {
                    "@id": "#library-501-sequencers",
                    "@type": "PropertyValue",
                    "name": "library_mv_sequencer_names",
                    "value": ["NovaSeq"],
                },
                {
                    "@id": "#library-501-input-value",
                    "@type": "PropertyValue",
                    "name": "library_mv_measured_value",
                    "value": 2,
                },
                {
                    "@id": "#library-501-input-unit",
                    "@type": "PropertyValue",
                    "name": "library_mv_measuring_unit",
                    "value": "ng/µl",
                },
                {
                    "@id": "#library-501-concentration",
                    "@type": "PropertyValue",
                    "name": "library_mv_concentration_library",
                    "value": 1.5,
                },
                {
                    "@id": "#library-501-create-time",
                    "@type": "PropertyValue",
                    "name": "library_mv_create_time",
                    "value": "2026-01-30T12:00:00Z",
                },
                {
                    "@id": "#organism-1",
                    "@type": "Thing",
                    "name": "Arabidopsis",
                },
                {
                    "@id": "#library-process-501",
                    "@type": "CreateAction",
                    "name": "Library metadata capture",
                    "object": [{"@id": "#library-material-501"}],
                    "result": [{"@id": "#library-data-501"}],
                },
                {
                    "@id": "#library-data-501",
                    "@type": "MediaObject",
                    "name": "Library export metadata",
                },
                {
                    "@id": "#library-assay-501",
                    "@type": "Dataset",
                    "name": "Assay for Delivered library",
                },
                {
                    "@id": "#request-context-102",
                    "@type": "Dataset",
                    "name": "102_Second Request",
                },
                {
                    "@id": "#study-102",
                    "@type": "Dataset",
                    "name": "Study for 102_Second Request",
                    "materials": {"samples": [{"@id": "#sample-material-502"}]},
                },
                {
                    "@id": "#sample-material-502",
                    "@type": "Thing",
                    "name": "Second sample",
                    "identifier": "26L000502",
                    "additionalType": {"@id": "https://w3id.org/isa/Sample"},
                    "additionalProperty": [{"@id": "#sample-502-name"}],
                },
                {
                    "@id": "#sample-502-name",
                    "@type": "PropertyValue",
                    "name": "sample_db_name",
                    "value": "Second sample",
                },
            ],
        },
    }


def _ro_crate_preview_payload_with_records(record_count):
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": "Parkour RO-Crate export",
            "hasPart": [{"@id": "#request-context-101"}, {"@id": "#study-101"}],
        },
        {
            "@id": "#request-context-101",
            "@type": "Dataset",
            "name": "101_ROCrate Request",
        },
        {
            "@id": "#study-101",
            "@type": "Dataset",
            "name": "Study for 101_ROCrate Request",
            "materials": {
                "otherMaterials": [
                    {"@id": f"#library-material-{index}"}
                    for index in range(1, record_count + 1)
                ]
            },
        },
    ]
    for index in range(1, record_count + 1):
        graph.extend(
            [
                {
                    "@id": f"#library-material-{index}",
                    "@type": "Thing",
                    "name": f"Preview library {index:02d}",
                    "identifier": f"26L{index:06d}",
                    "additionalType": {"@id": "https://w3id.org/isa/Library"},
                    "additionalProperty": [{"@id": f"#library-{index}-name"}],
                },
                {
                    "@id": f"#library-{index}-name",
                    "@type": "PropertyValue",
                    "name": "library_db_name",
                    "value": f"Preview library {index:02d}",
                },
            ]
        )
    return {
        "archive_name": "101_ro_crate.zip",
        "skipped_records": [],
        "ro_crate": {
            "@context": ["https://w3id.org/ro/crate/1.1/context"],
            "@graph": graph,
        },
    }


def _route_ro_crate_export_api(
    page: Page, seen_generate_requests=None, preview_payload=None
):
    def handle_generate_ro_crate(route):
        parsed = urlparse(route.request.url)
        query = parse_qs(parsed.query)
        if seen_generate_requests is not None:
            seen_generate_requests.append(query)
        if query.get("pdf") == ["true"]:
            route.fulfill(
                body=b"%PDF-1.4\n% test pdf\n",
                headers={
                    "content-type": "application/pdf",
                    "content-disposition": 'attachment; filename="101_ro_crate.pdf"',
                },
            )
            return
        route.fulfill(json=preview_payload or _ro_crate_preview_payload())

    page.route("**/api/generate_ro_crate/**", handle_generate_ro_crate)


def test_requests_page(page: Page):
    _open_batch_add_modal(page)
    description_textarea = page.get_by_test_id("request-description-input")
    description_textarea.fill("Automated UI smoke test")

    add_records_button = page.get_by_test_id("add-records-button")
    add_records_button.click()

    rows = page.locator("#requestEditorDraftTable .tabulator-row")
    expect(rows).to_have_count(1)

    _close_batch_add_modal(page)


def test_ro_crate_action_requires_exportable_selection(page: Page):
    utilities.pretest_login(page)
    utilities.visit_vue_page(page, "libraries_and_samples")
    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )

    page.get_by_test_id("open-ro-crate-preview-button").click()
    expect(
        page.get_by_text(
            "Select at least one library or sample in Sequencing or Delivered "
            "status for RO-Crate export."
        )
    ).to_be_visible(timeout=5000)


def test_ro_crate_action_allows_sequencing_selection(page: Page):
    _open_libraries_page_with_ro_crate_data(page, status=5)
    _route_ro_crate_export_api(page)
    _select_first_ro_crate_row(page)

    expect(page.get_by_test_id("ro-crate-preview-overlay")).to_be_visible()


def test_ro_crate_preview_opens_with_expected_api_params(page: Page):
    seen_generate_requests = []

    _open_libraries_page_with_ro_crate_data(page)
    _route_ro_crate_export_api(page, seen_generate_requests)
    _select_first_ro_crate_row(page)

    preview_overlay = page.get_by_test_id("ro-crate-preview-overlay")
    expect(preview_overlay).to_be_visible()
    expect(
        preview_overlay.get_by_role("link", name="RO-Crate Documentation")
    ).to_be_visible()
    expect(
        preview_overlay.get_by_text("Selected Libraries & Samples")
    ).to_be_visible()
    expect(
        preview_overlay.get_by_text("Request 1: 101_ROCrate Request")
    ).to_be_visible()
    expect(preview_overlay.get_by_text("Preview request description")).to_be_visible()
    expect(preview_overlay.get_by_text("QC Completed At", exact=True)).to_have_count(0)
    expect(preview_overlay.get_by_text("Request 2: 102_Second Request")).to_be_visible()
    expect(preview_overlay.get_by_text("Library: Delivered library")).to_be_visible()
    expect(preview_overlay.get_by_text("Sample: Second sample")).to_be_visible()
    expect(preview_overlay.get_by_text("Barcode: 26L000501")).to_be_visible()
    expect(preview_overlay.get_by_text("Barcode: 26L000502*")).to_be_visible()
    overview_chip = preview_overlay.locator(".record-chip").filter(
        has_text="26L000501: Delivered library"
    )
    expect(overview_chip).to_be_visible()
    overview_chip.click()
    expect(
        preview_overlay.locator(".record-table-block").filter(
            has_text="Library: Delivered library"
        )
    ).to_be_focused()
    expect(preview_overlay.get_by_text("Preparation", exact=True)).to_have_count(2)
    expect(preview_overlay.get_by_text("Sequencing", exact=True)).to_have_count(2)
    expect(preview_overlay.get_by_text("Overview", exact=True)).to_have_count(0)
    expect(preview_overlay.get_by_text("Status", exact=True)).to_have_count(0)
    expect(preview_overlay.get_by_text("S/L", exact=True)).to_have_count(0)
    expect(preview_overlay.get_by_text("Organism", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("Arabidopsis", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("2 ng/µl", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("1.500", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("Date", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("30.01.2026", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("Length", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("2x150", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("Flowcell IDs", exact=True)).to_be_visible()
    expect(preview_overlay.get_by_text("FC001", exact=True)).to_be_visible()
    expect(
        preview_overlay.get_by_text("Library 1: Delivered library")
    ).not_to_be_visible()

    assert seen_generate_requests
    query = seen_generate_requests[0]
    assert query["barcodes"] == ["26L000501"]
    assert query["preview"] == ["true"]
    assert "sections" not in query


def test_ro_crate_preview_renders_all_libraries_and_samples(page: Page):
    _open_libraries_page_with_ro_crate_data(page)
    _route_ro_crate_export_api(
        page,
        preview_payload=_ro_crate_preview_payload_with_records(21),
    )
    _select_first_ro_crate_row(page)

    preview_overlay = page.get_by_test_id("ro-crate-preview-overlay")
    expect(preview_overlay).to_be_visible()
    expect(preview_overlay.get_by_text("Showing first")).to_have_count(0)
    expect(preview_overlay.get_by_text("Library: Preview library 20")).to_be_visible()
    expect(preview_overlay.get_by_text("Library: Preview library 21")).to_be_visible()


def test_ro_crate_pdf_export_uses_backend_pdf_download(page: Page):
    seen_generate_requests = []

    _open_libraries_page_with_ro_crate_data(page)
    _route_ro_crate_export_api(page, seen_generate_requests)
    _select_first_ro_crate_row(page)

    preview_overlay = page.get_by_test_id("ro-crate-preview-overlay")
    expect(preview_overlay).to_be_visible()

    with page.expect_download() as download_info:
        preview_overlay.get_by_test_id("export-ro-crate-pdf-button").click()

    download = download_info.value
    assert download.suggested_filename == "101_ro_crate.pdf"
    assert seen_generate_requests[-1]["pdf"] == ["true"]
    assert "preview" not in seen_generate_requests[-1]


def test_ro_crate_preview_displays_backend_error(page: Page):
    _open_libraries_page_with_ro_crate_data(page)
    page.route(
        "**/api/generate_ro_crate/**",
        lambda route: route.fulfill(
            status=400,
            json={"error": "RO-Crate preview failed."},
        ),
    )
    _select_first_ro_crate_row(page)

    expect(page.get_by_test_id("ro-crate-preview-overlay")).to_be_visible()
    expect(page.get_by_text("RO-Crate preview failed.")).to_be_visible()
