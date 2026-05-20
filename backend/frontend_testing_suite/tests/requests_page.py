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


def _mock_libraries_and_samples_for_ro_crate(page: Page):
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
                        "name": "Delivered library",
                        "barcode": "26L000501",
                        "status": 6,
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


def _open_libraries_page_with_ro_crate_data(page: Page):
    utilities.pretest_login(page)
    _mock_libraries_and_samples_for_ro_crate(page)
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
    page.get_by_test_id("open-ro-crate-popup-button").click()
    expect(page.get_by_test_id("ro-crate-export-modal")).to_be_visible()


def _ro_crate_preview_payload():
    return {
        "archive_name": "101_ROCrate_Request_ro_crate.zip",
        "skipped_records": [],
        "ro_crate": {
            "@context": ["https://w3id.org/ro/crate/1.2/context", {"@base": "./"}],
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"},
                },
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "101_ROCrate Request",
                    "hasPart": [{"@id": "#library-material-501"}],
                },
                {
                    "@id": "#library-material-501",
                    "@type": "Thing",
                    "name": "Delivered library",
                    "identifier": "26L000501",
                    "additionalType": {"@id": "https://w3id.org/isa/Library"},
                    "additionalProperty": [
                        {
                            "@type": "PropertyValue",
                            "name": "library_db_name",
                            "value": "Delivered library",
                        }
                    ],
                },
            ],
        },
    }


def test_requests_page(page: Page):
    _open_batch_add_modal(page)
    description_textarea = page.get_by_test_id("request-description-input")
    description_textarea.fill("Automated UI smoke test")

    add_records_button = page.get_by_test_id("add-records-button")
    add_records_button.click()

    rows = page.locator("#requestEditorDraftTable .tabulator-row")
    expect(rows).to_have_count(1)

    _close_batch_add_modal(page)


def test_ro_crate_action_requires_delivered_selection(page: Page):
    utilities.pretest_login(page)
    utilities.visit_vue_page(page, "libraries_and_samples")
    utilities.expect_page_header(
        page,
        "Libraries & Samples",
        preferred_test_id="libraries-header-title",
    )

    page.get_by_test_id("open-ro-crate-popup-button").click()
    expect(
        page.get_by_text(
            "Select at least one delivered library or sample for RO-Crate export."
        )
    ).to_be_visible(timeout=5000)


def test_ro_crate_export_dialog_section_controls(page: Page):
    _open_libraries_page_with_ro_crate_data(page)
    _select_first_ro_crate_row(page)

    preview_button = page.get_by_test_id("preview-ro-crate-button")
    expect(preview_button).to_be_enabled()

    page.get_by_test_id("ro-crate-clear-sections-button").click()
    expect(page.get_by_test_id("ro-crate-validation-message")).to_have_text(
        "Select at least one information section to include in the RO-Crate."
    )
    expect(preview_button).to_be_disabled()

    page.get_by_test_id("ro-crate-select-all-sections-button").click()
    expect(page.get_by_test_id("ro-crate-section-request")).to_be_checked()
    expect(page.get_by_test_id("ro-crate-section-libraries")).to_be_checked()
    expect(preview_button).to_be_enabled()


def test_ro_crate_preview_opens_with_expected_api_params(page: Page):
    seen_generate_requests = []

    _open_libraries_page_with_ro_crate_data(page)

    def handle_generate_ro_crate(route):
        parsed = urlparse(route.request.url)
        seen_generate_requests.append(parse_qs(parsed.query))
        route.fulfill(json=_ro_crate_preview_payload())

    page.route("**/api/generate_ro_crate/**", handle_generate_ro_crate)
    _select_first_ro_crate_row(page)

    page.get_by_test_id("ro-crate-clear-sections-button").click()
    page.get_by_test_id("ro-crate-section-request").check()
    page.get_by_test_id("ro-crate-section-libraries").check()
    page.get_by_test_id("preview-ro-crate-button").click()

    preview_overlay = page.get_by_test_id("ro-crate-preview-overlay")
    expect(preview_overlay).to_be_visible()
    expect(preview_overlay.get_by_text("Delivered library")).to_be_visible()
    expect(preview_overlay.get_by_text("26L000501")).to_be_visible()

    assert seen_generate_requests
    query = seen_generate_requests[0]
    assert query["barcodes"] == ["26L000501"]
    assert query["preview"] == ["true"]
    assert query["sections"] == ["request,libraries"]


def test_ro_crate_preview_displays_backend_error(page: Page):
    _open_libraries_page_with_ro_crate_data(page)
    page.route(
        "**/api/generate_ro_crate/**",
        lambda route: route.fulfill(
            status=400,
            json={"error": "Unknown RO-Crate section value."},
        ),
    )
    _select_first_ro_crate_row(page)

    page.get_by_test_id("preview-ro-crate-button").click()

    expect(page.get_by_test_id("ro-crate-preview-overlay")).to_be_visible()
    expect(page.get_by_text("Unknown RO-Crate section value.")).to_be_visible()
