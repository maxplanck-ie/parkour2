import json
import mimetypes
import os
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from itertools import chain
from zipfile import ZIP_DEFLATED, ZipFile

from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.db.models.fields.files import FieldFile
from django.http import HttpResponse
from django.utils import timezone
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from rest_framework import viewsets
from rest_framework.response import Response

from .utils import get_accessible_requests

Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")
CompleteSampleData = apps.get_model("sample", "CompleteSampleData")
Pooling = apps.get_model("pooling", "Pooling")
LibraryPreparation = apps.get_model("library_preparation", "LibraryPreparation")
Flowcell = apps.get_model("flowcell", "Flowcell")
IndexPool = apps.get_model("index_generator", "Pool")
IndexPair = apps.get_model("library_sample_shared", "IndexPair")

RO_CRATE_VERSION = "1.1"
RO_CRATE_SPEC_URI = f"https://w3id.org/ro/crate/{RO_CRATE_VERSION}"
RO_CRATE_CONTEXT_URI = f"{RO_CRATE_SPEC_URI}/context"
NFDI4PLANTS_ISA_PROFILE_URI = (
    "https://github.com/nfdi4plants/isa-ro-crate-profile/tree/release/profile"
)
ISA_NAMESPACE_URI = "https://w3id.org/isa/"
ISA_INVESTIGATION_URI = f"{ISA_NAMESPACE_URI}Investigation"
ISA_STUDY_URI = f"{ISA_NAMESPACE_URI}Study"
ISA_ASSAY_URI = f"{ISA_NAMESPACE_URI}Assay"
ISA_PROCESS_URI = f"{ISA_NAMESPACE_URI}Process"
ISA_DATA_URI = f"{ISA_NAMESPACE_URI}Data"
ISA_MATERIAL_URI = f"{ISA_NAMESPACE_URI}Material"
ISA_SAMPLE_URI = f"{ISA_NAMESPACE_URI}Sample"
ISA_LIBRARY_URI = f"{ISA_NAMESPACE_URI}Library"
ISA_ORGANISM_URI = f"{ISA_NAMESPACE_URI}Organism"
ISA_PROTOCOL_URI = f"{ISA_NAMESPACE_URI}Protocol"
ISA_POOL_URI = f"{ISA_NAMESPACE_URI}Pool"
ISA_LANE_URI = f"{ISA_NAMESPACE_URI}Lane"

PARKOUR_ORGANIZATION_ID = "#parkour-organization"
PARKOUR_SOFTWARE_ID = "#parkour-software"
RO_CRATE_EXPORT_ACTION_ID = "#ro-crate-export-action"
RO_CRATE_LICENSE_ID = "#parkour-ro-crate-license"
RO_CRATE_ROOT_ID = "./"
RO_CRATE_COMPLETED_STATUS = 6
RO_CRATE_ARCHIVE_STUB_MAX_LENGTH = 180
RO_CRATE_EXPORT_FILENAME_MAX_LENGTH = 50

RO_CRATE_SECTION_IDS = {
    "request",
    "samples",
    "libraries",
    "library_preparation",
    "pooling",
    "protocols",
    "organisms",
    "library_types",
    "read_lengths",
    "index_types",
    "nucleic_acid_types",
    "index_pools",
    "flowcells",
    "sequencers",
    "lanes",
}

PATH_REFERENCE_VALUE_KEYS = ("path",)
PATH_REFERENCE_MD5_KEYS = ("md5",)
PATH_REFERENCE_IGNORED_ALIAS_KEYS = {
    "filepath",
    "file_path",
    "contentUrl",
    "url",
    "value",
    "MD5",
    "md5_hash",
    "md5Hash",
    "checksum_md5",
    "checksumMd5",
    "checksum",
}


def _normalise_field_policy_key(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _load_shared_hidden_fields():
    module_dir = os.path.dirname(__file__)
    policy_paths = [
        os.path.abspath(
            os.path.join(module_dir, "..", "shared", "roCrateHiddenFields.json")
        ),
        os.path.abspath(
            os.path.join(module_dir, "..", "..", "shared", "roCrateHiddenFields.json")
        ),
    ]
    policy_path = next((path for path in policy_paths if os.path.exists(path)), None)
    if policy_path is None:
        raise RuntimeError(
            "RO-Crate hidden field policy file could not be loaded. Searched: "
            + ", ".join(policy_paths)
        )

    try:
        with open(policy_path, encoding="utf-8") as handle:
            policy = json.load(handle)
    except OSError as exc:
        raise RuntimeError(
            "RO-Crate hidden field policy file could not be loaded."
        ) from exc
    except ValueError as exc:
        raise RuntimeError("RO-Crate hidden field policy is not valid JSON.") from exc

    hidden_fields = policy.get("userDefinedVariableHiddenFields")
    if not isinstance(hidden_fields, list):
        raise RuntimeError(
            "RO-Crate hidden field policy must define userDefinedVariableHiddenFields."
        )
    return {_normalise_field_policy_key(field) for field in hidden_fields if field}


RO_CRATE_HIDDEN_FIELD_KEYS = _load_shared_hidden_fields()


def _is_comment_export_field(field_name):
    normalised = _normalise_field_policy_key(field_name)
    return (
        normalised.endswith("comment") or normalised.endswith("comments")
    ) and normalised not in {"usercomment", "usercomments"}


def _is_hidden_export_field(*field_names):
    return any(
        _normalise_field_policy_key(field_name) in RO_CRATE_HIDDEN_FIELD_KEYS
        or _is_comment_export_field(field_name)
        for field_name in field_names
        if field_name
    )


@dataclass
class ExportSelection:
    barcode_values: list
    request_values: list
    selected_sections: set
    preview_requested: bool
    pdf_requested: bool
    accessible_requests: object
    library_rows: list
    sample_rows: list
    missing_barcodes: list
    missing_requests: list
    skipped_records: list
    target_request_ids: list


@dataclass
class CrateBuildResult:
    ro_crate: dict
    archive_name: str
    file_entries: list


def _parse_csv_values(raw_value):
    if not raw_value:
        return []
    return [item.strip() for item in str(raw_value).split(",") if item.strip()]


def _normalise_sections(raw_sections):
    if raw_sections is None:
        return set(RO_CRATE_SECTION_IDS)

    selected = _parse_csv_values(raw_sections)
    if not selected:
        return Response({"error": "Select at least one RO-Crate section."}, status=400)

    invalid = sorted(set(selected) - RO_CRATE_SECTION_IDS)
    if invalid:
        return Response(
            {"error": "Unknown RO-Crate section value.", "invalid_sections": invalid},
            status=400,
        )
    return set(selected)


def _normalise_true_flag(raw_value, query_name):
    if raw_value is None:
        return False
    if raw_value == "true":
        return True
    return Response(
        {"error": f"The '{query_name}' query parameter must be 'true' when provided."},
        status=400,
    )


def _normalise_preview(raw_preview):
    return _normalise_true_flag(raw_preview, "preview")


def _normalise_pdf(raw_pdf):
    return _normalise_true_flag(raw_pdf, "pdf")


def _normalise_property_value(value):
    if value in (None, "", [], {}):
        return None
    if isinstance(value, FieldFile):
        return value.name or None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        values = [
            normalised
            for normalised in (_normalise_property_value(item) for item in value)
            if normalised not in (None, "", [], {})
        ]
        return values or None
    if isinstance(value, dict):
        values = {
            key: normalised
            for key, normalised in (
                (key, _normalise_property_value(nested))
                for key, nested in value.items()
            )
            if normalised not in (None, "", [], {})
        }
        return values or None
    return value


def _related_object_export_value(value):
    if value in (None, ""):
        return None
    for attr_name in ("name", "title", "label", "username"):
        attr_value = getattr(value, attr_name, None)
        if attr_value not in (None, ""):
            return _normalise_property_value(attr_value)
    return str(value)


def _first_mapping_value(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _normalise_path_metadata_value(value):
    if value in (None, "", [], {}):
        return None

    if isinstance(value, dict):
        path_value = _first_mapping_value(value, PATH_REFERENCE_VALUE_KEYS)
        md5_value = _first_mapping_value(value, PATH_REFERENCE_MD5_KEYS)
        if path_value is not None or md5_value is not None:
            result = {}
            if path_value is not None:
                result["path"] = _normalise_property_value(path_value)
            if md5_value is not None:
                result["md5"] = _normalise_property_value(md5_value)
            return result or None

        result = {}
        for key, nested_value in value.items():
            if key in PATH_REFERENCE_IGNORED_ALIAS_KEYS:
                continue
            normalised = _normalise_path_metadata_value(nested_value)
            if normalised not in (None, "", [], {}):
                result[key] = normalised
        return result or None

    if isinstance(value, (list, tuple, set)):
        values = [
            normalised
            for normalised in (_normalise_path_metadata_value(item) for item in value)
            if normalised not in (None, "", [], {})
        ]
        return values or None

    return _normalise_property_value(value)


def _comment(name, value, section=None):
    normalised = _normalise_property_value(value)
    if normalised in (None, "", [], {}):
        return None
    entry = {"name": name, "value": normalised}
    if section:
        entry["_section"] = section
    return entry


def _comments_from_mapping(mapping, section=None):
    comments = []
    seen = set()
    for name, value in mapping.items():
        if _is_hidden_export_field(name):
            continue
        entry = _comment(name, value, section)
        if not entry:
            continue
        key = (entry["name"], json.dumps(entry["value"], sort_keys=True, default=str))
        if key in seen:
            continue
        seen.add(key)
        comments.append(entry)
    return comments


def _record_property_metadata(instance, prefix):
    if instance is None:
        return {}
    metadata = {}
    for field_name in ("index_i7_id", "index_i5_id"):
        value = getattr(instance, field_name, None)
        if value not in (None, "", [], {}):
            metadata[f"{prefix}{field_name}"] = value
    return metadata


def _index_pair_metadata(index_pair):
    if index_pair is None:
        return {}
    metadata = _extract_model_fields(index_pair, "index_pair_")
    coordinate = getattr(index_pair, "coordinate", None)
    if coordinate not in (None, "", [], {}):
        metadata["index_pair_coordinate"] = coordinate
    return metadata


def _clean_comments(comments):
    cleaned = []
    seen = set()
    for entry in comments or []:
        if not entry:
            continue
        public_entry = {
            "name": entry.get("name"),
            "value": _normalise_property_value(entry.get("value")),
        }
        if public_entry["value"] in (None, "", [], {}):
            continue
        key = (
            public_entry["name"],
            json.dumps(public_entry["value"], sort_keys=True, default=str),
        )
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(public_entry)
    return cleaned


def _extract_model_fields(instance, prefix="", section=None, exclude_fields=None):
    if instance is None:
        return {}
    exclude_fields = set(exclude_fields or [])
    data = {}
    for field in instance._meta.concrete_fields:
        field_name = field.name
        if field_name == "archived" or field_name in exclude_fields:
            continue
        export_name = (
            field_name[len("removed_") :]
            if field_name.startswith("removed_")
            else field_name
        )
        target_name = f"{prefix}{export_name}"
        if _is_hidden_export_field(field_name, export_name, target_name):
            continue
        try:
            value = (
                _related_object_export_value(getattr(instance, field_name, None))
                if getattr(field, "remote_field", None)
                else field.value_from_object(instance)
            )
        except Exception:  # pragma: no cover - defensive around model descriptors
            continue
        if target_name not in data:
            data[target_name] = value
    return data


def _request_metadata(request_obj):
    metadata = _extract_model_fields(request_obj, prefix="request_")
    for source_field, target_key in (
        ("filepaths", "request_filepaths"),
        ("metapaths", "request_metapaths"),
    ):
        if _is_hidden_export_field(source_field, target_key):
            continue
        paths = _normalise_path_metadata_value(getattr(request_obj, source_field, None))
        if paths not in (None, "", [], {}):
            metadata[target_key] = json.dumps(paths, sort_keys=True, default=str)
    deep_seq_request = getattr(request_obj, "deep_seq_request", None)
    if deep_seq_request:
        metadata["request_deep_seq_request"] = deep_seq_request.name
    return metadata


def _safe_archive_component(value, fallback):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "")).strip("._")
    return cleaned or fallback


def _request_file_folder_name(request_obj):
    request_id = str(request_obj.id)
    return _safe_archive_component(
        request_obj.name,
        f"request-{request_id}",
    )


def _archive_stub(requests_by_id, request_ids):
    ids = [
        str(request_id) for request_id in request_ids if request_id in requests_by_id
    ]
    if not ids:
        return "parkour"
    stub = "_".join(ids)
    return stub[:RO_CRATE_ARCHIVE_STUB_MAX_LENGTH].rstrip("._-") or "parkour"


def _bounded_export_filename(base_name, extension):
    extension = extension if str(extension).startswith(".") else f".{extension}"
    max_base_length = max(1, RO_CRATE_EXPORT_FILENAME_MAX_LENGTH - len(extension))
    safe_base = _safe_archive_component(base_name, "parkour_ro_crate")
    safe_base = safe_base[:max_base_length].rstrip("._-") or "parkour_ro_crate"
    return f"{safe_base}{extension}"


def _ro_crate_archive_name(archive_stub):
    return _bounded_export_filename(f"{archive_stub}_ro_crate", ".zip")


def _ro_crate_pdf_name(archive_name):
    pdf_base = re.sub(r"\.(zip|pdf)$", "", str(archive_name or ""), flags=re.I)
    return _bounded_export_filename(pdf_base, ".pdf")


def _parkour_identifier(entity_type, value):
    if value in (None, ""):
        return None
    return f"urn:parkour:{entity_type}:{value}"


def _ref(entity_id):
    return {"@id": entity_id}


def _unique_refs(refs):
    result = []
    seen = set()
    for ref in refs or []:
        ref_id = ref.get("@id") if isinstance(ref, dict) else None
        if not ref_id or ref_id in seen:
            continue
        seen.add(ref_id)
        result.append({"@id": ref_id})
    return result


def _property_value_id(owner_id, property_name, name, value):
    value_key = json.dumps(value, sort_keys=True, default=str)
    stable_id = uuid.uuid5(
        uuid.NAMESPACE_URL, f"{owner_id}:{property_name}:{name}:{value_key}"
    )
    safe_name = _safe_archive_component(name, "property")
    return f"{owner_id}-{property_name}-{safe_name}-{stable_id.hex[:10]}"


def _add_additional_type(entity, *type_ids):
    values = entity.setdefault("additionalType", [])
    if isinstance(values, dict):
        values = [values]
    elif not isinstance(values, list):
        values = [values]
    existing = {item.get("@id") if isinstance(item, dict) else item for item in values}
    for type_id in type_ids:
        if type_id and type_id not in existing:
            values.append({"@id": type_id})
            existing.add(type_id)
    entity["additionalType"] = values


def _guess_encoding_format(filename):
    guessed_type, _ = mimetypes.guess_type(filename or "")
    return guessed_type or "application/octet-stream"


def _request_file_archive_path(file_obj, request_obj):
    original_name = getattr(getattr(file_obj, "file", None), "name", None)
    base_name = os.path.basename(original_name or file_obj.name or "")
    request_folder = _request_file_folder_name(request_obj)
    file_name = _safe_archive_component(base_name, f"request_file_{file_obj.id}")
    return f"request-files/{request_folder}/{file_obj.id}_{file_name}"


def _select_records(request):
    barcodes = _parse_csv_values(request.query_params.get("barcodes"))
    requests = _parse_csv_values(request.query_params.get("requests"))
    sections = _normalise_sections(request.query_params.get("sections"))
    if isinstance(sections, Response):
        return sections
    preview = _normalise_preview(request.query_params.get("preview"))
    if isinstance(preview, Response):
        return preview
    pdf = _normalise_pdf(request.query_params.get("pdf"))
    if isinstance(pdf, Response):
        return pdf
    if not barcodes and not requests:
        return Response(
            {
                "error": (
                    "Provide at least one comma separated barcode value or request "
                    "name via the 'barcodes' or 'requests' query parameters."
                )
            },
            status=400,
        )

    accessible_requests = get_accessible_requests(request)
    accessible_ids = list(accessible_requests.values_list("id", flat=True))
    library_qs = CompleteLibraryData.objects.filter(request_id__in=accessible_ids)
    sample_qs = CompleteSampleData.objects.filter(request_id__in=accessible_ids)

    filters = Q()
    if barcodes:
        filters |= Q(barcode__in=barcodes)
    if requests:
        filters |= Q(request_name__in=requests)
    library_rows = list(library_qs.filter(filters))
    sample_rows = list(sample_qs.filter(filters))

    found_barcodes = {row.barcode for row in chain(library_rows, sample_rows)}
    missing_barcodes = sorted(
        barcode for barcode in barcodes if barcode not in found_barcodes
    )

    delivered_libraries, skipped_libraries = _split_delivered(library_rows)
    delivered_samples, skipped_samples = _split_delivered(sample_rows)
    skipped_records = sorted(set(skipped_libraries + skipped_samples))
    if skipped_records and not delivered_libraries and not delivered_samples:
        return Response(
            {
                "error": "RO-Crate export requires selected libraries or samples to have Delivered status.",
                "skipped_records": skipped_records,
            },
            status=400,
        )

    request_qs = accessible_requests.filter(name__in=requests)
    found_request_names = set(request_qs.values_list("name", flat=True))
    missing_requests = sorted(
        request_name
        for request_name in requests
        if request_name not in found_request_names
    )
    request_ids_from_names = set(request_qs.values_list("id", flat=True))
    request_ids_from_rows = {
        row.request_id for row in chain(delivered_libraries, delivered_samples)
    }

    return ExportSelection(
        barcode_values=barcodes,
        request_values=requests,
        selected_sections=sections,
        preview_requested=preview,
        pdf_requested=pdf,
        accessible_requests=accessible_requests,
        library_rows=delivered_libraries,
        sample_rows=delivered_samples,
        missing_barcodes=missing_barcodes,
        missing_requests=missing_requests,
        skipped_records=skipped_records,
        target_request_ids=sorted(request_ids_from_names | request_ids_from_rows),
    )


def _split_delivered(rows):
    delivered = []
    skipped = []
    for row in rows:
        if getattr(row, "status", None) == RO_CRATE_COMPLETED_STATUS:
            delivered.append(row)
        else:
            skipped.append(
                getattr(row, "barcode", None) or getattr(row, "name", None) or str(row)
            )
    return delivered, skipped


def _requests_by_id(accessible_requests, request_ids):
    return {
        request_obj.id: request_obj
        for request_obj in accessible_requests.filter(id__in=request_ids)
    }


class SimpleROCrateBuilder:
    def __init__(self, request, selection):
        self.request = request
        self.selection = selection
        self.now = timezone.now()
        self.graph = []
        self.entities = {}
        self.file_entries = []
        self.root_refs = []
        self.has_part_refs = []

    def build(self):
        requests_by_id = _requests_by_id(
            self.selection.accessible_requests, self.selection.target_request_ids
        )
        if not requests_by_id:
            return self._empty_result()

        root_request = requests_by_id[self.selection.target_request_ids[0]]
        self.requests_by_id = requests_by_id
        self.library_models = self._library_models()
        self.sample_models = self._sample_models()
        self._extend_requests_with_record_memberships()
        self.library_preparations = self._library_preparations()
        self.pooling_by_library, self.pooling_by_sample = self._pooling()

        self._add_static_entities()
        self._add_root_dataset(root_request)
        self._add_request_entities()
        self._add_sample_entities()
        self._add_library_entities()
        self._add_flowcell_entities()
        self._finalise_root_links()
        self._materialise_comments_as_property_values()

        ro_crate = {
            "@context": [RO_CRATE_CONTEXT_URI, self._context()],
            "@graph": self.graph,
        }
        ro_crate = _filter_sections(ro_crate, self.selection.selected_sections)
        archive_name = _ro_crate_archive_name(
            _archive_stub(requests_by_id, self.selection.target_request_ids)
        )
        file_entries = [
            entry
            for entry in self.file_entries
            if any(
                graph_entry.get("contentUrl") == entry[0]
                for graph_entry in ro_crate.get("@graph", [])
            )
        ]
        return CrateBuildResult(ro_crate, archive_name, file_entries)

    def _empty_result(self):
        now_iso = self.now.isoformat()
        ro_crate = {
            "@context": [RO_CRATE_CONTEXT_URI],
            "@graph": [
                _metadata_descriptor(),
                {
                    "@id": RO_CRATE_ROOT_ID,
                    "@type": "Dataset",
                    "name": "Parkour RO-Crate export",
                    "identifier": _parkour_identifier("ro-crate-export", now_iso),
                    "description": "No matching barcodes or requests were found.",
                    "datePublished": self.now.date().isoformat(),
                    "conformsTo": [_ref(RO_CRATE_SPEC_URI)],
                    "publisher": _ref(PARKOUR_ORGANIZATION_ID),
                },
                _parkour_organization(),
            ],
        }
        return CrateBuildResult(ro_crate, _ro_crate_archive_name("parkour"), [])

    def _library_models(self):
        ids = [row.library_id for row in self.selection.library_rows]
        return {
            library.id: library
            for library in Library.objects.filter(id__in=ids)
            .select_related(
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            )
            .prefetch_related(
                "request",
                "index_type__indices_i7",
                "index_type__indices_i5",
                "library_type__library_protocol",
            )
        }

    def _sample_models(self):
        ids = [row.sample_id for row in self.selection.sample_rows]
        return {
            sample.id: sample
            for sample in Sample.objects.filter(id__in=ids)
            .select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            )
            .prefetch_related(
                "request",
                "index_type__indices_i7",
                "index_type__indices_i5",
                "library_type__library_protocol",
            )
        }

    def _extend_requests_with_record_memberships(self):
        related_request_ids = set()
        for model in chain(self.library_models.values(), self.sample_models.values()):
            try:
                related_request_ids.update(
                    request_id
                    for request_id in model.request.values_list("id", flat=True)
                    if request_id
                )
            except Exception:
                continue
        missing_request_ids = related_request_ids - set(self.requests_by_id)
        if not missing_request_ids:
            return
        accessible_missing_requests = _requests_by_id(
            self.selection.accessible_requests, missing_request_ids
        )
        self.requests_by_id.update(accessible_missing_requests)
        self.selection.target_request_ids = sorted(
            set(self.selection.target_request_ids) | set(accessible_missing_requests)
        )

    def _library_preparations(self):
        sample_ids = [row.sample_id for row in self.selection.sample_rows]
        if not sample_ids:
            return {}
        return {
            prep.sample_id: prep
            for prep in LibraryPreparation.objects.filter(sample_id__in=sample_ids)
        }

    def _pooling(self):
        library_ids = [row.library_id for row in self.selection.library_rows]
        sample_ids = [row.sample_id for row in self.selection.sample_rows]
        by_library = {}
        by_sample = {}
        if not library_ids and not sample_ids:
            return by_library, by_sample
        for pooling in Pooling.objects.filter(
            Q(library_id__in=library_ids) | Q(sample_id__in=sample_ids)
        ):
            if pooling.library_id:
                by_library[pooling.library_id] = pooling
            if pooling.sample_id:
                by_sample[pooling.sample_id] = pooling
        return by_library, by_sample

    def _add(self, entity, section=None):
        if section:
            entity["_section"] = section
        entity_id = entity.get("@id")
        if entity_id in self.entities:
            self.entities[entity_id].update(
                {
                    key: value
                    for key, value in entity.items()
                    if value not in (None, "", [], {})
                }
            )
            return self.entities[entity_id]
        self.entities[entity_id] = entity
        self.graph.append(entity)
        return entity

    def _mention(self, entity_id):
        self.root_refs.append(_ref(entity_id))

    def _has_part(self, entity_id):
        self.has_part_refs.append(_ref(entity_id))

    def _add_property_values(self, owner, property_name, values, section):
        owner_id = owner.get("@id")
        if not owner_id:
            return

        if isinstance(values, dict):
            entries = _comments_from_mapping(values, section)
        else:
            entries = values or []

        refs = []
        for entry in entries:
            name = entry.get("name") if isinstance(entry, dict) else None
            value = entry.get("value") if isinstance(entry, dict) else None
            if not name or _is_hidden_export_field(name):
                continue
            if name in {"request_filepaths", "request_metapaths"} and isinstance(
                value, str
            ):
                try:
                    value = json.loads(value)
                except ValueError:
                    pass
            normalised_value = _normalise_property_value(value)
            if normalised_value in (None, "", [], {}):
                continue
            if isinstance(normalised_value, dict):
                normalised_value = json.dumps(
                    normalised_value, sort_keys=True, default=str
                )

            entity_id = _property_value_id(
                owner_id, property_name, name, normalised_value
            )
            value_section = (
                entry.get("_section") if isinstance(entry, dict) else None
            ) or section
            self._add(
                {
                    "@id": entity_id,
                    "@type": "PropertyValue",
                    "name": name,
                    "value": normalised_value,
                },
                value_section,
            )
            refs.append(_ref(entity_id))

        if refs:
            owner[property_name] = _unique_refs(owner.get(property_name, []) + refs)

    def _materialise_comments_as_property_values(self):
        for entity in list(self.graph):
            comments = entity.pop("comments", None)
            if not comments:
                continue
            property_name = (
                "parameterValue"
                if self._is_create_action(entity)
                else "additionalProperty"
            )
            self._add_property_values(
                entity,
                property_name,
                comments,
                entity.get("_section") or _entity_section(entity),
            )

    def _is_create_action(self, entity):
        entity_type = entity.get("@type")
        if isinstance(entity_type, list):
            return "CreateAction" in entity_type
        return entity_type == "CreateAction"

    def _add_static_entities(self):
        self._add(_metadata_descriptor())
        self._add(_parkour_organization())
        self._add(
            {
                "@id": NFDI4PLANTS_ISA_PROFILE_URI,
                "@type": "CreativeWork",
                "name": "NFDI4Plants ISA RO-Crate profile",
                "url": NFDI4PLANTS_ISA_PROFILE_URI,
            }
        )
        self._add(
            {
                "@id": PARKOUR_SOFTWARE_ID,
                "@type": "SoftwareApplication",
                "name": "Parkour LIMS",
                "softwareVersion": str(getattr(settings, "VERSION", "")) or None,
                "url": "https://github.com/maxplanck-ie/parkour2",
            }
        )
        self._add(
            {
                "@id": RO_CRATE_LICENSE_ID,
                "@type": "CreativeWork",
                "name": "Parkour metadata export terms",
                "description": (
                    "This RO-Crate is generated from Parkour and reflects metadata "
                    "available to the exporting user at export time."
                ),
            }
        )
        self._add(
            {
                "@id": RO_CRATE_EXPORT_ACTION_ID,
                "@type": "CreateAction",
                "name": "Parkour RO-Crate export generation",
                "instrument": _ref(PARKOUR_SOFTWARE_ID),
                "agent": _ref(PARKOUR_SOFTWARE_ID),
                "object": [_ref(RO_CRATE_ROOT_ID)],
                "result": [],
                "endTime": self.now.isoformat(),
            }
        )

    def _add_root_dataset(self, root_request):
        is_multi = len(self.selection.target_request_ids) > 1
        root_name = (
            f"Parkour RO-Crate export ({len(self.selection.target_request_ids)} requests)"
            if is_multi
            else root_request.name or f"Request {root_request.id}"
        )
        comments = _comments_from_mapping(_request_metadata(root_request), "request")
        comments.extend(
            _comments_from_mapping(
                {
                    "requested_barcodes": ", ".join(self.selection.barcode_values),
                    "requested_requests": ", ".join(self.selection.request_values),
                    "missing_barcodes": ", ".join(self.selection.missing_barcodes),
                    "missing_requests": ", ".join(self.selection.missing_requests),
                    "skipped_non_delivered_records": ", ".join(
                        self.selection.skipped_records
                    ),
                },
                "request",
            )
        )
        root = self._add(
            {
                "@id": RO_CRATE_ROOT_ID,
                "@type": "Dataset",
                "name": root_name,
                "identifier": (
                    _parkour_identifier(
                        "ro-crate-export",
                        "-".join(str(pk) for pk in self.selection.target_request_ids),
                    )
                    if is_multi
                    else _parkour_identifier("request", root_request.id)
                ),
                "description": (
                    f"Parkour metadata export for {len(self.selection.target_request_ids)} selected requests."
                    if is_multi
                    else root_request.description or ""
                ),
                "dateCreated": _normalise_property_value(
                    getattr(root_request, "create_time", None)
                )
                or self.now.isoformat(),
                "datePublished": self.now.date().isoformat(),
                "conformsTo": [_ref(RO_CRATE_SPEC_URI)],
                "additionalType": [_ref(ISA_INVESTIGATION_URI), "Investigation"],
                "license": _ref(RO_CRATE_LICENSE_ID),
                "creator": _ref(PARKOUR_SOFTWARE_ID),
                "publisher": _ref(PARKOUR_ORGANIZATION_ID),
                "comments": comments,
                "mentions": [],
                "hasPart": [],
            },
            "request",
        )
        self.root = root
        self._add_property_values(root, "additionalProperty", comments, "request")

    def _add_request_entities(self):
        for request_obj in self.requests_by_id.values():
            request_context_id = f"#request-context-{request_obj.id}"
            request_metadata = _request_metadata(request_obj)
            request_context = self._add(
                {
                    "@id": request_context_id,
                    "@type": "Dataset",
                    "name": request_obj.name or f"Request {request_obj.id}",
                    "identifier": _parkour_identifier("request", request_obj.id),
                    "description": request_obj.description or "",
                    "comments": _comments_from_mapping(request_metadata, "request"),
                },
                "request",
            )
            self._add_property_values(
                request_context, "additionalProperty", request_metadata, "request"
            )
            self._mention(request_context_id)
            self._has_part(request_context_id)
            self._add_study(request_obj)
            self._add_request_files(request_obj)

    def _add_study(self, request_obj):
        study_id = f"#study-{request_obj.id}"
        study = self._add(
            {
                "@id": study_id,
                "@type": "Dataset",
                "name": f"Study for {request_obj.name or f'Request {request_obj.id}'}",
                "identifier": _parkour_identifier("study", request_obj.id),
                "description": request_obj.description or "",
                "dateCreated": _normalise_property_value(
                    getattr(request_obj, "create_time", None)
                ),
                "datePublished": self.now.date().isoformat(),
                "additionalType": [_ref(ISA_STUDY_URI)],
                "materials": {
                    "sources": [],
                    "samples": [],
                    "otherMaterials": [],
                },
                "assays": [],
                "processSequence": [],
                "dataFiles": [],
                "hasPart": [],
                "about": [],
            },
            "request",
        )
        self._mention(study_id)
        self._has_part(study_id)
        return study

    def _add_request_files(self, request_obj):
        for request_file in request_obj.files.all():
            file_field = getattr(request_file, "file", None)
            try:
                disk_path = file_field.path if file_field else None
            except Exception:
                disk_path = None
            if not disk_path or not os.path.exists(disk_path):
                continue

            archive_path = _request_file_archive_path(request_file, request_obj)
            entity_id = f"#request-file-{request_file.id}"
            self.file_entries.append((archive_path, disk_path))
            self._add(
                {
                    "@id": entity_id,
                    "@type": ["File", "MediaObject"],
                    "name": request_file.name
                    or getattr(file_field, "name", None)
                    or f"Request file {request_file.id}",
                    "identifier": _parkour_identifier("request-file", request_file.id),
                    "contentUrl": archive_path,
                    "encodingFormat": _guess_encoding_format(
                        getattr(file_field, "name", None) or request_file.name
                    ),
                    "isPartOf": _ref(RO_CRATE_ROOT_ID),
                    "about": _ref(f"#study-{request_obj.id}"),
                    "requestContext": _ref(f"#request-context-{request_obj.id}"),
                    "comments": _comments_from_mapping(
                        {
                            "request_file_name": request_file.name,
                            "request_file_storage_path": getattr(
                                file_field, "name", None
                            ),
                        },
                        "request",
                    ),
                },
                "request",
            )
            self._mention(entity_id)
            self._has_part(entity_id)

    def _add_sample_entities(self):
        for row in self.selection.sample_rows:
            model = self.sample_models.get(row.sample_id)
            source_id = f"#source-sample-{row.sample_id}"
            sample_id = f"#sample-material-{row.sample_id}"
            process_id = f"#sample-process-{row.sample_id}"
            data_id = f"#sample-data-{row.sample_id}"
            assay_id = f"#sample-assay-{row.sample_id}"

            self._add(
                {
                    "@id": source_id,
                    "@type": "Thing",
                    "name": f"Source for {row.name}",
                    "identifier": _parkour_identifier("source-sample", row.sample_id),
                    "additionalType": [_ref(ISA_MATERIAL_URI)],
                    "comments": _comments_from_mapping(
                        {"source_request_identifier": row.request_name}, "samples"
                    ),
                },
                "samples",
            )

            comments = []
            if model:
                comments.extend(
                    _comments_from_mapping(
                        _extract_model_fields(model, "sample_db_"), "samples"
                    )
                )
                comments.extend(
                    _comments_from_mapping(
                        _record_property_metadata(model, "sample_db_"), "samples"
                    )
                )
            sample_mv_comments = _comments_from_mapping(
                _extract_model_fields(row, "sample_mv_"), "samples"
            )
            prep = self.library_preparations.get(row.sample_id)
            if prep:
                comments.extend(
                    _comments_from_mapping(
                        _extract_model_fields(prep, "library_preparation_"),
                        "library_preparation",
                    )
                )
            pooling = self.pooling_by_sample.get(row.sample_id)
            if pooling:
                comments.extend(
                    _comments_from_mapping(
                        _extract_model_fields(pooling, "pooling_"), "pooling"
                    )
                )

            sample = self._add(
                {
                    "@id": sample_id,
                    "@type": "Thing",
                    "name": row.name,
                    "identifier": row.barcode,
                    "additionalType": [
                        _ref(ISA_MATERIAL_URI),
                        _ref(ISA_SAMPLE_URI),
                        _ref("https://bioschemas.org/Sample"),
                    ],
                    "derivedFrom": [_ref(source_id)],
                    "comments": comments,
                },
                "samples",
            )
            self._add_property_values(sample, "additionalProperty", comments, "samples")
            self._link_biology_terms(sample, model)
            self._link_index_metadata(sample, model, row, "samples")
            pool_refs = self._index_pool_refs(model)
            if pool_refs:
                sample["associatedPool"] = pool_refs

            self._add_process(
                process_id,
                f"Sample metadata capture for {row.name}",
                "sample-process",
                row.sample_id,
                [_ref(source_id)],
                [_ref(sample_id), _ref(data_id)],
                model,
                "samples",
                comments=sample_mv_comments,
                parameter_values=sample_mv_comments,
            )
            self._add_data(
                data_id,
                f"Sample export metadata for {row.name}",
                "sample-data",
                row.sample_id,
                "samples",
            )
            self._add_assay(
                assay_id,
                f"Assay for sample {row.name}",
                sample_id,
                process_id,
                data_id,
                "samples",
            )
            record_entity_ids = [source_id, sample_id, process_id, data_id, assay_id]
            self._link_to_record_requests(
                sample, model, row.request_id, record_entity_ids
            )

    def _add_library_entities(self):
        for row in self.selection.library_rows:
            model = self.library_models.get(row.library_id)
            library_id = f"#library-material-{row.library_id}"
            process_id = f"#library-process-{row.library_id}"
            data_id = f"#library-data-{row.library_id}"
            assay_id = f"#library-assay-{row.library_id}"

            comments = []
            if model:
                comments.extend(
                    _comments_from_mapping(
                        _extract_model_fields(model, "library_db_"), "libraries"
                    )
                )
                comments.extend(
                    _comments_from_mapping(
                        _record_property_metadata(model, "library_db_"), "libraries"
                    )
                )
            pooling = self.pooling_by_library.get(row.library_id)
            if pooling:
                comments.extend(
                    _comments_from_mapping(
                        _extract_model_fields(pooling, "pooling_"), "pooling"
                    )
                )

            library = self._add(
                {
                    "@id": library_id,
                    "@type": "Thing",
                    "name": row.name,
                    "identifier": row.barcode,
                    "additionalType": [_ref(ISA_MATERIAL_URI), _ref(ISA_LIBRARY_URI)],
                    "comments": comments,
                },
                "libraries",
            )
            self._add_property_values(
                library, "additionalProperty", comments, "libraries"
            )
            self._link_biology_terms(library, model)
            self._link_index_metadata(library, model, row, "libraries")
            pool_refs = self._index_pool_refs(model)
            if pool_refs:
                library["associatedPool"] = pool_refs

            library_mv_comments = _comments_from_mapping(
                _extract_model_fields(row, "library_mv_"), "libraries"
            )
            self._add_process(
                process_id,
                f"Library metadata capture for {row.name}",
                "library-process",
                row.library_id,
                [_ref(library_id)],
                [_ref(data_id)],
                model,
                "libraries",
                comments=library_mv_comments,
                parameter_values=library_mv_comments,
            )
            self._add_data(
                data_id,
                f"Library export metadata for {row.name}",
                "library-data",
                row.library_id,
                "libraries",
            )
            self._add_assay(
                assay_id,
                f"Assay for library {row.name}",
                library_id,
                process_id,
                data_id,
                "libraries",
            )
            self._link_to_record_requests(
                library,
                model,
                row.request_id,
                [library_id, process_id, data_id, assay_id],
            )

    def _add_process(
        self,
        entity_id,
        name,
        identifier_type,
        identifier_value,
        inputs,
        outputs,
        model,
        section,
        comments=None,
        parameter_values=None,
    ):
        entity = {
            "@id": entity_id,
            "@type": "CreateAction",
            "name": name,
            "identifier": _parkour_identifier(identifier_type, identifier_value),
            "additionalType": [
                _ref(ISA_PROCESS_URI),
                _ref("https://bioschemas.org/LabProcess"),
            ],
            "object": inputs,
            "result": outputs,
            "comments": comments or [],
        }
        if getattr(model, "library_protocol", None):
            protocol_id = self._add_protocol(model.library_protocol)
            entity["executesLabProtocol"] = _ref(protocol_id)
        process_entity = self._add(entity, section)
        self._add_property_values(
            process_entity,
            "parameterValue",
            parameter_values or comments or [],
            section,
        )

    def _add_data(self, entity_id, name, identifier_type, identifier_value, section):
        self._add(
            {
                "@id": entity_id,
                "@type": "MediaObject",
                "name": name,
                "identifier": _parkour_identifier(identifier_type, identifier_value),
                "additionalType": [_ref(ISA_DATA_URI)],
                "encodingFormat": "application/json",
            },
            section,
        )

    def _add_assay(self, entity_id, name, material_id, process_id, data_id, section):
        self._add(
            {
                "@id": entity_id,
                "@type": "Dataset",
                "name": name,
                "identifier": _parkour_identifier("assay", entity_id.strip("#")),
                "additionalType": [_ref(ISA_ASSAY_URI)],
                "hasPart": [_ref(material_id), _ref(data_id)],
                "about": [_ref(process_id)],
                "variableMeasured": "metadata export",
                "measurementMethod": "Parkour LIMS metadata capture",
            },
            section,
        )

    def _link_biology_terms(self, entity, model):
        if not model:
            return
        links = (
            ("organism", "organism", "organisms", ISA_ORGANISM_URI),
            ("libraryType", "library_type", "library_types", ISA_MATERIAL_URI),
            ("readLength", "read_length", "read_lengths", None),
            ("indexType", "index_type", "index_types", None),
            (
                "nucleicAcidType",
                "nucleic_acid_type",
                "nucleic_acid_types",
                ISA_MATERIAL_URI,
            ),
        )
        for property_name, attr_name, section, additional_type in links:
            value = getattr(model, attr_name, None)
            if not value:
                continue
            entity_id = f"#{attr_name.replace('_', '-')}-{value.id}"
            term = self._add(
                {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": getattr(value, "name", None) or str(value),
                    "identifier": _parkour_identifier(
                        attr_name.replace("_", "-"), value.id
                    ),
                    "comments": _comments_from_mapping(
                        _extract_model_fields(value, f"{attr_name}_"), section
                    ),
                },
                section,
            )
            if additional_type:
                _add_additional_type(term, additional_type)
            if attr_name == "library_type":
                try:
                    self._link_library_type_protocols(term, value)
                except Exception:
                    pass
            entity[property_name] = _ref(entity_id)
            self._mention(entity_id)

    def _link_library_type_protocols(self, library_type_entity, library_type):
        protocol_refs = []
        for protocol in library_type.library_protocol.all():
            protocol_id = self._add_protocol(protocol)
            protocol_refs.append(_ref(protocol_id))
        if protocol_refs:
            library_type_entity["availableProtocols"] = _unique_refs(
                library_type_entity.get("availableProtocols", []) + protocol_refs
            )

    def _link_index_metadata(self, entity, model, row, section):
        if not model or not getattr(model, "index_type", None):
            return
        try:
            i7_entity_id = self._selected_index_entity_id(model, "i7")
            i5_entity_id = self._selected_index_entity_id(model, "i5")
            index_pair = self._selected_index_pair(model, row)
        except Exception:
            return
        if i7_entity_id:
            entity["indexI7"] = _ref(i7_entity_id)
        if i5_entity_id:
            entity["indexI5"] = _ref(i5_entity_id)
        if index_pair:
            entity["selectedIndexPair"] = _ref(
                self._add_index_pair(index_pair, section)
            )

    def _selected_index_entity_id(self, model, index_kind):
        index_type = getattr(model, "index_type", None)
        sequence = getattr(model, f"index_{index_kind}", None)
        if not index_type or not sequence:
            return None
        relation_name = "indices_i7" if index_kind == "i7" else "indices_i5"
        for index_obj in getattr(index_type, relation_name).all():
            if index_obj.index == sequence:
                return self._add_index_sequence(index_obj, index_kind)
        return None

    def _selected_index_pair(self, model, row):
        index_type = getattr(model, "index_type", None)
        if not index_type:
            return None
        coordinate = str(getattr(row, "coordinate", "") or "").strip()
        query = IndexPair.objects.filter(index_type=index_type).select_related(
            "index_type", "index1", "index2"
        )
        if coordinate:
            char_coord = coordinate[:1]
            num_coord = coordinate[1:]
            if char_coord and num_coord.isdigit():
                return query.filter(
                    char_coord=char_coord,
                    num_coord=int(num_coord),
                ).first()
        index_i7 = getattr(model, "index_i7", None)
        index_i5 = getattr(model, "index_i5", None)
        if index_i7:
            query = query.filter(index1__index=index_i7)
        if index_i5:
            query = query.filter(index2__index=index_i5)
        return query.first()

    def _add_index_sequence(self, index_obj, index_kind):
        entity_id = f"#index-{index_kind}-{index_obj.id}"
        self._add(
            {
                "@id": entity_id,
                "@type": "Thing",
                "name": index_obj.index_id or str(index_obj),
                "identifier": _parkour_identifier(f"index-{index_kind}", index_obj.id),
                "indexSequence": index_obj.index,
                "comments": _comments_from_mapping(
                    _extract_model_fields(index_obj, f"index_{index_kind}_"),
                    "index_types",
                ),
            },
            "index_types",
        )
        self._mention(entity_id)
        return entity_id

    def _add_index_pair(self, index_pair, section):
        entity_id = f"#index-pair-{index_pair.id}"
        try:
            index_pair_name = str(index_pair)
        except Exception:
            index_pair_name = f"Index pair {index_pair.id}"
        entity = {
            "@id": entity_id,
            "@type": "Thing",
            "name": index_pair_name,
            "identifier": _parkour_identifier("index-pair", index_pair.id),
            "coordinate": index_pair.coordinate,
            "indexType": _ref(f"#index-type-{index_pair.index_type_id}")
            if index_pair.index_type_id
            else None,
            "indexI7": _ref(self._add_index_sequence(index_pair.index1, "i7"))
            if index_pair.index1
            else None,
            "indexI5": _ref(self._add_index_sequence(index_pair.index2, "i5"))
            if index_pair.index2
            else None,
            "comments": _comments_from_mapping(
                _index_pair_metadata(index_pair), "index_types"
            ),
        }
        self._add(
            entity, "index_types" if section in {"libraries", "samples"} else section
        )
        self._mention(entity_id)
        return entity_id

    def _add_protocol(self, protocol):
        protocol_id = f"#protocol-{protocol.id}"
        entity = self._add(
            {
                "@id": protocol_id,
                "@type": "HowTo",
                "name": protocol.name or str(protocol),
                "identifier": _parkour_identifier("protocol", protocol.id),
                "additionalType": [
                    _ref(ISA_PROTOCOL_URI),
                    _ref("https://bioschemas.org/LabProtocol"),
                ],
                "comments": _comments_from_mapping(
                    _extract_model_fields(protocol, "protocol_"), "protocols"
                ),
            },
            "protocols",
        )
        self._mention(entity["@id"])
        return protocol_id

    def _add_pool_size(self, pool_size):
        if not pool_size:
            return None
        entity_id = f"#index-pool-size-{pool_size.id}"
        self._add(
            {
                "@id": entity_id,
                "@type": "Thing",
                "name": pool_size.name,
                "identifier": _parkour_identifier("index-pool-size", pool_size.id),
                "comments": _comments_from_mapping(
                    _extract_model_fields(pool_size, "index_pool_size_"),
                    "index_pools",
                ),
            },
            "index_pools",
        )
        self._mention(entity_id)
        return entity_id

    def _add_index_pool(self, pool):
        if not pool:
            return None
        pool_id = f"#index-pool-{pool.id}"
        member_refs = []
        for library in pool.libraries.all():
            if library.id in self.library_models:
                member_refs.append(_ref(f"#library-material-{library.id}"))
        for sample in pool.samples.all():
            if sample.id in self.sample_models:
                member_refs.append(_ref(f"#sample-material-{sample.id}"))
        comments = _comments_from_mapping(
            {
                "index_pool_loaded": pool.loaded,
                "index_pool_comment": pool.comment,
                "index_pool_total_sequencing_depth": pool.total_sequencing_depth,
            },
            "index_pools",
        )
        pool_size_id = None
        if getattr(pool, "size", None):
            pool_size_id = self._add_pool_size(pool.size)
            comments.extend(
                _comments_from_mapping(
                    _extract_model_fields(pool.size, "index_pool_size_"),
                    "index_pools",
                )
            )
        self._add(
            {
                "@id": pool_id,
                "@type": "Thing",
                "name": pool.name or f"Pool {pool.id}",
                "identifier": _parkour_identifier("index-pool", pool.id),
                "additionalType": [_ref(ISA_POOL_URI)],
                "member": _unique_refs(member_refs),
                "poolSize": _ref(pool_size_id) if pool_size_id else None,
                "comments": comments,
            },
            "index_pools",
        )
        self._mention(pool_id)
        return pool_id

    def _index_pool_refs(self, model):
        if not model:
            return []
        refs = []
        qs = IndexPool.objects.none()
        if isinstance(model, Library):
            qs = IndexPool.objects.filter(libraries__id=model.id)
        elif isinstance(model, Sample):
            qs = IndexPool.objects.filter(samples__id=model.id)
        for pool in qs.distinct():
            pool_id = self._add_index_pool(pool)
            if pool_id:
                refs.append(_ref(pool_id))
        return _unique_refs(refs)

    def _add_flowcell_entities(self):
        flowcells = (
            Flowcell.objects.filter(requests__id__in=self.selection.target_request_ids)
            .select_related("sequencer")
            .prefetch_related(
                "requests",
                "lanes__pool__size",
                "lanes__pool__libraries",
                "lanes__pool__samples",
            )
            .distinct()
        )
        for flowcell in flowcells:
            flowcell_id = f"#flowcell-assay-{flowcell.id}"
            data_id = f"#flowcell-data-{flowcell.id}"
            process_id = f"#flowcell-process-{flowcell.id}"
            flowcell_data_refs = [_ref(data_id)]
            lane_refs = []
            record_ids_on_flowcell = set()
            for lane in flowcell.lanes.all():
                lane_id = f"#lane-{lane.id}"
                lane_refs.append(_ref(lane_id))
                lane_pool_id = self._add_index_pool(lane.pool)
                if lane.pool:
                    record_ids_on_flowcell.update(
                        f"#library-material-{library_id}"
                        for library_id in lane.pool.libraries.values_list(
                            "id", flat=True
                        )
                        if library_id in self.library_models
                    )
                    record_ids_on_flowcell.update(
                        f"#sample-material-{sample_id}"
                        for sample_id in lane.pool.samples.values_list("id", flat=True)
                        if sample_id in self.sample_models
                    )
                self._add(
                    {
                        "@id": lane_id,
                        "@type": "Thing",
                        "name": lane.name or f"Lane {lane.id}",
                        "identifier": _parkour_identifier("lane", lane.id),
                        "additionalType": [_ref(ISA_LANE_URI)],
                        "associatedPool": _ref(lane_pool_id) if lane_pool_id else None,
                        "comments": _comments_from_mapping(
                            {
                                "lane_loading_concentration": lane.loading_concentration,
                                "lane_phix": lane.phix,
                                "lane_completed": lane.completed,
                                "lane_name": lane.name,
                            },
                            "lanes",
                        ),
                    },
                    "lanes",
                )
                self._mention(lane_id)

            sequencer_ref = None
            if flowcell.sequencer:
                sequencer_id = f"#sequencer-{flowcell.sequencer.id}"
                sequencer_ref = _ref(sequencer_id)
                self._add(
                    {
                        "@id": sequencer_id,
                        "@type": "Thing",
                        "name": flowcell.sequencer.name or str(flowcell.sequencer),
                        "identifier": _parkour_identifier(
                            "sequencer", flowcell.sequencer.id
                        ),
                        "comments": _comments_from_mapping(
                            _extract_model_fields(flowcell.sequencer, "sequencer_"),
                            "sequencers",
                        ),
                    },
                    "sequencers",
                )
                self._mention(sequencer_id)

            comments = _comments_from_mapping(
                _extract_model_fields(
                    flowcell,
                    "flowcell_",
                    exclude_fields={"matrix", "sequences"},
                ),
                "flowcells",
            )
            self._add(
                {
                    "@id": data_id,
                    "@type": "MediaObject",
                    "name": f"Flowcell export metadata for {flowcell.flowcell_id}",
                    "identifier": _parkour_identifier("flowcell-data", flowcell.id),
                    "additionalType": [_ref(ISA_DATA_URI)],
                    "encodingFormat": "application/json",
                    "comments": comments,
                },
                "flowcells",
            )
            for field_name, label in (
                ("matrix", "matrix"),
                ("sequences", "sequences"),
            ):
                value = getattr(flowcell, field_name, None)
                if value in (None, "", [], {}):
                    continue
                entity_id = f"#flowcell-{label}-data-{flowcell.id}"
                self._add(
                    {
                        "@id": entity_id,
                        "@type": "MediaObject",
                        "name": f"Flowcell {flowcell.flowcell_id} {label}",
                        "identifier": _parkour_identifier(
                            f"flowcell-{label}-data", flowcell.id
                        ),
                        "additionalType": [_ref(ISA_DATA_URI)],
                        "encodingFormat": "application/json",
                        "comments": _comments_from_mapping(
                            {f"flowcell_{field_name}": value}, "flowcells"
                        ),
                    },
                    "flowcells",
                )
                flowcell_data_refs.append(_ref(entity_id))
            process = {
                "@id": process_id,
                "@type": "CreateAction",
                "name": f"Sequencing metadata capture for flowcell {flowcell.flowcell_id}",
                "identifier": _parkour_identifier("flowcell-process", flowcell.id),
                "additionalType": [_ref(ISA_PROCESS_URI)],
                "object": lane_refs,
                "result": flowcell_data_refs,
                "comments": comments,
            }
            if sequencer_ref:
                process["instrument"] = sequencer_ref
                process["hasInstrument"] = sequencer_ref
            self._add(process, "flowcells")
            assay = {
                "@id": flowcell_id,
                "@type": "Dataset",
                "name": f"Flowcell {flowcell.flowcell_id}",
                "identifier": _parkour_identifier("flowcell-assay", flowcell.id),
                "additionalType": [_ref(ISA_ASSAY_URI)],
                "hasPart": lane_refs + flowcell_data_refs,
                "hasLane": lane_refs,
                "about": [_ref(process_id)],
                "variableMeasured": "sequencing",
                "measurementMethod": "flowcell loading",
            }
            if sequencer_ref:
                assay["instrument"] = sequencer_ref
                assay["hasInstrument"] = sequencer_ref
            self._add(assay, "flowcells")
            for record_id in record_ids_on_flowcell:
                record_entity = self.entities.get(record_id)
                if record_entity:
                    record_entity["sequencedOn"] = _unique_refs(
                        record_entity.get("sequencedOn", []) + [_ref(flowcell_id)]
                    )
            for request_obj in flowcell.requests.all():
                if request_obj.id in self.requests_by_id:
                    self._link_to_study(
                        request_obj.id,
                        [flowcell_id, process_id]
                        + [ref["@id"] for ref in flowcell_data_refs],
                    )

    def _link_to_study(self, request_id, entity_ids):
        study = self.entities.get(f"#study-{request_id}")
        if study:
            study["hasPart"] = _unique_refs(
                study.get("hasPart", []) + [_ref(entity_id) for entity_id in entity_ids]
            )
            for entity_id in entity_ids:
                if entity_id.startswith("#source-sample-"):
                    self._add_material_ref(study, "sources", entity_id)
                elif entity_id.startswith("#sample-material-"):
                    self._add_material_ref(study, "samples", entity_id)
                elif entity_id.startswith("#library-material-"):
                    self._add_material_ref(study, "otherMaterials", entity_id)
                elif self._is_process_id(entity_id):
                    self._add_study_ref(study, "processSequence", entity_id)
                    self._add_study_ref(study, "about", entity_id)
                elif self._is_assay_id(entity_id):
                    self._add_study_ref(study, "assays", entity_id)
                elif self._is_data_id(entity_id):
                    self._add_study_ref(study, "dataFiles", entity_id)
        for entity_id in entity_ids:
            self._mention(entity_id)

    def _link_to_record_requests(self, entity, model, fallback_request_id, entity_ids):
        request_ids = self._record_request_ids(model, fallback_request_id)
        entity["requestContext"] = _unique_refs(
            entity.get("requestContext", [])
            + [_ref(f"#request-context-{request_id}") for request_id in request_ids]
        )
        for request_id in request_ids:
            self._link_to_study(request_id, entity_ids)

    def _record_request_ids(self, model, fallback_request_id):
        request_ids = {fallback_request_id}
        if model:
            request_ids.update(
                request_id
                for request_id in model.request.values_list("id", flat=True)
                if request_id in self.requests_by_id
            )
        return sorted(
            request_id
            for request_id in request_ids
            if request_id in self.requests_by_id
        )

    def _add_material_ref(self, study, material_key, entity_id):
        materials = study.setdefault("materials", {})
        materials[material_key] = _unique_refs(
            materials.get(material_key, []) + [_ref(entity_id)]
        )

    def _add_study_ref(self, study, property_name, entity_id):
        study[property_name] = _unique_refs(
            study.get(property_name, []) + [_ref(entity_id)]
        )

    def _is_process_id(self, entity_id):
        return "-process-" in entity_id or entity_id.endswith("-process")

    def _is_assay_id(self, entity_id):
        return entity_id.startswith(
            ("#sample-assay-", "#library-assay-", "#flowcell-assay-")
        )

    def _is_data_id(self, entity_id):
        return entity_id.startswith(
            (
                "#sample-data-",
                "#library-data-",
                "#flowcell-data-",
                "#flowcell-matrix-data-",
                "#flowcell-sequences-data-",
            )
        )

    def _finalise_root_links(self):
        self._mention(RO_CRATE_EXPORT_ACTION_ID)
        self.root["mentions"] = _unique_refs(self.root_refs)
        self.root["hasPart"] = _unique_refs(self.has_part_refs)
        export_action = self.entities.get(RO_CRATE_EXPORT_ACTION_ID)
        if export_action:
            export_action["object"] = [_ref(RO_CRATE_ROOT_ID)]
            export_action["result"] = _unique_refs(
                [_ref("ro-crate-metadata.json")] + self.has_part_refs
            )

    def _context(self):
        return {
            "Dataset": "http://schema.org/Dataset",
            "CreativeWork": "http://schema.org/CreativeWork",
            "CreateAction": "http://schema.org/CreateAction",
            "File": "http://schema.org/MediaObject",
            "MediaObject": "http://schema.org/MediaObject",
            "Thing": "http://schema.org/Thing",
            "HowTo": "http://schema.org/HowTo",
            "Person": "http://schema.org/Person",
            "Organization": "http://schema.org/Organization",
            "SoftwareApplication": "http://schema.org/SoftwareApplication",
            "PropertyValue": "http://schema.org/PropertyValue",
            "DefinedTerm": "http://schema.org/DefinedTerm",
            "additionalType": "http://schema.org/additionalType",
            "value": "http://schema.org/value",
            "additionalProperty": {
                "@id": "http://schema.org/additionalProperty",
                "@type": "@id",
            },
            "materials": "https://w3id.org/isa/materials",
            "sources": {"@id": "https://w3id.org/isa/sources", "@type": "@id"},
            "samples": {"@id": "https://w3id.org/isa/samples", "@type": "@id"},
            "otherMaterials": {
                "@id": "https://w3id.org/isa/otherMaterials",
                "@type": "@id",
            },
            "assays": {"@id": "https://w3id.org/isa/assays", "@type": "@id"},
            "processSequence": {
                "@id": "https://w3id.org/isa/processSequence",
                "@type": "@id",
            },
            "dataFiles": {"@id": "https://w3id.org/isa/dataFiles", "@type": "@id"},
            "derivedFrom": {"@id": "https://w3id.org/isa/derivesFrom", "@type": "@id"},
            "executesLabProtocol": {
                "@id": "https://bioschemas.org/executesLabProtocol",
                "@type": "@id",
            },
            "hasPart": {"@id": "http://schema.org/hasPart", "@type": "@id"},
            "mentions": {"@id": "http://schema.org/mentions", "@type": "@id"},
            "object": {"@id": "http://schema.org/object", "@type": "@id"},
            "result": {"@id": "http://schema.org/result", "@type": "@id"},
            "parameterValue": {
                "@id": "https://bioschemas.org/parameterValue",
                "@type": "@id",
            },
            "member": {"@id": "http://schema.org/member", "@type": "@id"},
            "poolSize": {"@id": "http://schema.org/size", "@type": "@id"},
            "hasInstrument": {
                "@id": "https://w3id.org/isa/hasInstrument",
                "@type": "@id",
            },
            "hasLane": {"@id": "https://w3id.org/isa/hasPart", "@type": "@id"},
            "softwareVersion": "http://schema.org/softwareVersion",
            "organism": {"@id": "http://schema.org/taxonomicRange", "@type": "@id"},
            "libraryType": {"@id": "http://schema.org/additionalType", "@type": "@id"},
            "readLength": {
                "@id": "http://schema.org/measurementTechnique",
                "@type": "@id",
            },
            "indexType": {"@id": "http://schema.org/category", "@type": "@id"},
            "indexI7": {"@id": "http://schema.org/identifier", "@type": "@id"},
            "indexI5": {"@id": "http://schema.org/identifier", "@type": "@id"},
            "selectedIndexPair": {
                "@id": "http://schema.org/isRelatedTo",
                "@type": "@id",
            },
            "availableProtocols": {
                "@id": "https://bioschemas.org/executesLabProtocol",
                "@type": "@id",
            },
            "indexSequence": "http://schema.org/value",
            "coordinate": "http://schema.org/position",
            "nucleicAcidType": {"@id": "http://schema.org/material", "@type": "@id"},
            "associatedPool": {"@id": "http://schema.org/isRelatedTo", "@type": "@id"},
            "sequencedOn": {"@id": "http://schema.org/isRelatedTo", "@type": "@id"},
            "requestContext": {"@id": "http://schema.org/isPartOf", "@type": "@id"},
        }


def _metadata_descriptor():
    return {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": _ref(RO_CRATE_SPEC_URI),
        "about": _ref(RO_CRATE_ROOT_ID),
    }


def _parkour_organization():
    return {
        "@id": PARKOUR_ORGANIZATION_ID,
        "@type": "Organization",
        "name": "Parkour",
        "url": "https://github.com/maxplanck-ie/parkour2",
    }


def _entity_section(entity):
    entity_id = str(entity.get("@id") or "")
    if entity_id in {"ro-crate-metadata.json", RO_CRATE_ROOT_ID}:
        return None
    if entity_id.startswith("#request-context-") or entity_id.startswith(
        "#request-file-"
    ):
        return "request"
    if entity_id.startswith("#protocol-"):
        return "protocols"
    if entity_id.startswith("#organism-"):
        return "organisms"
    if entity_id.startswith("#library-type-"):
        return "library_types"
    if entity_id.startswith("#read-length-"):
        return "read_lengths"
    if entity_id.startswith("#index-type-"):
        return "index_types"
    if entity_id.startswith(("#index-i7-", "#index-i5-", "#index-pair-")):
        return "index_types"
    if entity_id.startswith("#nucleic-acid-type-"):
        return "nucleic_acid_types"
    if entity_id.startswith("#index-pool-"):
        return "index_pools"
    if entity_id.startswith("#flowcell-"):
        return "flowcells"
    if entity_id.startswith("#sequencer-"):
        return "sequencers"
    if entity_id.startswith("#lane-"):
        return "lanes"
    if entity_id.startswith("#library-"):
        return "libraries"
    if entity_id.startswith("#sample-") or entity_id.startswith("#source-sample-"):
        return "samples"
    return None


def _comment_section(comment):
    return comment.get("_section")


def _filter_refs(value, kept_ids):
    if isinstance(value, list):
        filtered = []
        for item in value:
            filtered_item = _filter_refs(item, kept_ids)
            if filtered_item in (None, {}, []):
                continue
            filtered.append(filtered_item)
        return filtered
    if isinstance(value, dict):
        ref_id = value.get("@id")
        if ref_id and str(ref_id).startswith("#") and ref_id not in kept_ids:
            return None
        return {
            key: filtered_value
            for key, filtered_value in (
                (key, _filter_refs(nested, kept_ids)) for key, nested in value.items()
            )
            if filtered_value not in (None, {}, [])
        }
    return value


def _filter_sections(ro_crate, selected_sections):
    graph = ro_crate.get("@graph", [])
    kept = []
    for entity in graph:
        section = entity.get("_section") or _entity_section(entity)
        if section and section not in selected_sections:
            continue
        kept.append(entity)

    kept_ids = {entity.get("@id") for entity in kept if entity.get("@id")}
    public_graph = []
    for entity in kept:
        cleaned = {}
        for key, value in entity.items():
            if key in {"_section", "comments"}:
                continue
            value = _filter_refs(value, kept_ids)
            if value in (None, "", [], {}):
                continue
            cleaned[key] = value
        public_graph.append(cleaned)
    ro_crate["@graph"] = public_graph
    return ro_crate


PDF_FIELD_ID = "@id"
PDF_FIELD_TYPE = "@type"
PDF_FIELD_NAME = "name"
PDF_FIELD_IDENTIFIER = "identifier"
PDF_FIELD_ADDITIONAL_PROPERTY = "additionalProperty"
PDF_FIELD_PARAMETER_VALUE = "parameterValue"
PDF_FIELD_VALUE = "value"
PDF_FIELD_MATERIALS = "materials"
PDF_FIELD_SAMPLES = "samples"
PDF_FIELD_OTHER_MATERIALS = "otherMaterials"
PDF_FIELD_CONTENT_URL = "contentUrl"
PDF_FIELD_IS_PART_OF = "isPartOf"
PDF_FIELD_REQUEST_CONTEXT = "requestContext"

PDF_HIDDEN_DIRECT_FIELDS = {
    PDF_FIELD_ID,
    PDF_FIELD_TYPE,
    "about",
    PDF_FIELD_ADDITIONAL_PROPERTY,
    "additionalType",
    "comment",
    "comments",
    "contentSize",
    "encodingFormat",
    "hasPart",
    PDF_FIELD_IDENTIFIER,
    "includedInDataCatalog",
    PDF_FIELD_IS_PART_OF,
    "mentions",
    "publisher",
    "sameAs",
    "subjectOf",
    "url",
}
PDF_RELATED_MODEL_HIDDEN_FIELDS = {"sample", "library"}
PDF_VISIBLE_ID_FIELDS = {"i7_id", "i5_id", "indexI7Id", "indexI5Id"}
PDF_NORMALISED_VISIBLE_ID_FIELDS = {
    _normalise_field_policy_key(field) for field in PDF_VISIBLE_ID_FIELDS
}
PDF_LINKED_MODEL_RELATION_FIELDS = [
    "organism",
    "nucleicAcidType",
    "libraryType",
    "readLength",
    "indexType",
    "indexI7",
    "indexI5",
    "selectedIndexPair",
    "associatedPool",
]
PDF_RELATION_LABELS = {
    "indexI7": "Selected I7 Index",
    "indexI5": "Selected I5 Index",
    "availableProtocols": "Available Protocols",
    "executesLabProtocol": "Protocol",
    "instrument": "Instrument",
    "hasInstrument": "Instrument",
    "hasLane": "Lane",
    "poolSize": "Pool Size",
    "member": "Members",
    "sequencedOn": "Sequenced On",
    "object": "Input",
    "result": "Output",
    "dataFiles": "Data",
    "processSequence": "Processes",
}
PDF_BACKLINK_PROPERTIES = {
    "object",
    "result",
    "hasPart",
    "about",
    "dataFiles",
    "processSequence",
}
PDF_HIDDEN_FIELD_PATTERNS = (
    re.compile(r"email", re.I),
    re.compile(r"telephone", re.I),
    re.compile(r"(^|_)token($|_)", re.I),
    re.compile(r"(^|_)status($|_)", re.I),
)
PDF_PROPERTY_LABEL_OVERRIDES = {
    "dateCreated": "Date Created",
    "datePublished": "Date Published",
    "request_filepaths": "External File Paths",
    "request_metapaths": "External Metadata Paths",
    "barcode": "Barcode",
    "identifier": "Barcode",
}
PDF_MODEL_DISPLAY_RULES = [
    {
        "model_name": "Library",
        "prefixes": ("library_db_",),
        "id_prefixes": ("#library-material-",),
    },
    {
        "model_name": "Sample",
        "prefixes": ("sample_db_",),
        "id_prefixes": ("#sample-material-",),
    },
    {"model_name": "LibraryPreparation", "prefixes": ("library_preparation_",)},
    {"model_name": "Pooling", "prefixes": ("pooling_",)},
    {"model_name": "Request", "prefixes": ("request_",)},
    {
        "model_name": "Flowcell",
        "prefixes": ("flowcell_",),
        "id_prefixes": ("#flowcell-",),
    },
    {"model_name": "Lane", "prefixes": ("lane_",), "id_prefixes": ("#lane-",)},
    {
        "model_name": "Sequencer",
        "prefixes": ("sequencer_",),
        "id_prefixes": ("#sequencer-",),
    },
    {
        "model_name": "IndexPool",
        "prefixes": ("index_pool_",),
        "id_prefixes": ("#index-pool-",),
    },
    {
        "model_name": "PoolSize",
        "prefixes": ("index_pool_size_",),
        "id_prefixes": ("#index-pool-size-",),
    },
    {
        "model_name": "Organism",
        "prefixes": ("organism_",),
        "id_prefixes": ("#organism-",),
    },
    {
        "model_name": "LibraryType",
        "prefixes": ("library_type_",),
        "id_prefixes": ("#library-type-",),
    },
    {
        "model_name": "ReadLength",
        "prefixes": ("read_length_",),
        "id_prefixes": ("#read-length-",),
    },
    {
        "model_name": "IndexType",
        "prefixes": ("index_type_",),
        "id_prefixes": ("#index-type-",),
    },
    {
        "model_name": "NucleicAcidType",
        "prefixes": ("nucleic_acid_type_",),
        "id_prefixes": ("#nucleic-acid-type-",),
    },
    {
        "model_name": "LibraryProtocol",
        "prefixes": ("protocol_",),
        "id_prefixes": ("#protocol-",),
    },
    {
        "model_name": "IndexI7",
        "prefixes": ("index_i7_",),
        "id_prefixes": ("#index-i7-",),
    },
    {
        "model_name": "IndexI5",
        "prefixes": ("index_i5_",),
        "id_prefixes": ("#index-i5-",),
    },
    {
        "model_name": "IndexPair",
        "prefixes": ("index_pair_",),
        "id_prefixes": ("#index-pair-",),
    },
    {
        "model_name": "CompleteLibraryData",
        "prefixes": ("library_mv_", "library_export_"),
        "summary_only": True,
    },
    {
        "model_name": "CompleteSampleData",
        "prefixes": ("sample_mv_", "sample_export_"),
        "summary_only": True,
    },
]
PDF_MODEL_SECTION_RULES = sorted(
    [
        (rule["model_name"], rule["prefixes"])
        for rule in PDF_MODEL_DISPLAY_RULES
        if not rule.get("summary_only")
    ],
    key=lambda rule: max(len(prefix) for prefix in rule[1]),
    reverse=True,
)
PDF_MODEL_ID_RULES = sorted(
    [
        (prefix, rule["model_name"])
        for rule in PDF_MODEL_DISPLAY_RULES
        for prefix in rule.get("id_prefixes", ())
    ],
    key=lambda rule: len(rule[0]),
    reverse=True,
)
PDF_PROPERTY_PREFIXES = sorted(
    {prefix for rule in PDF_MODEL_DISPLAY_RULES for prefix in rule["prefixes"]},
    key=len,
    reverse=True,
)
PDF_PROPERTY_PREFIX_PATTERN = re.compile(
    rf"^({'|'.join(re.escape(prefix) for prefix in PDF_PROPERTY_PREFIXES)})"
)
PDF_SUMMARY_PROPERTY_PREFIXES = tuple(
    prefix
    for rule in PDF_MODEL_DISPLAY_RULES
    if rule.get("summary_only")
    for prefix in rule["prefixes"]
)
PDF_REPEATED_DATA_OBJECT_FIELDS = {
    "associatedPool",
    "derivedFrom",
    "indexI7",
    "indexI5",
    "indexType",
    "libraryProtocol",
    "libraryType",
    "nucleicAcidType",
    "organism",
    "readLength",
    "requestContext",
    "selectedIndexPair",
    "sequencedOn",
}
PDF_REPEATED_DATA_OBJECT_KEYS = {
    f"dataobject{_normalise_field_policy_key(field)}"
    for field in PDF_REPEATED_DATA_OBJECT_FIELDS
}


def _pdf_label_for_field(field_name):
    if field_name in PDF_PROPERTY_LABEL_OVERRIDES:
        return PDF_PROPERTY_LABEL_OVERRIDES[field_name]
    label = PDF_PROPERTY_PREFIX_PATTERN.sub("", str(field_name or ""))
    label = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", label)
    label = re.sub(r"[_-]+", " ", label)
    label = re.sub(r"\s+", " ", label).strip()
    return label.title()


def _pdf_is_hidden_field(field_name):
    key = str(field_name or "")
    normalised = _normalise_field_policy_key(key)
    prefixless = PDF_PROPERTY_PREFIX_PATTERN.sub("", key)
    prefixless_normalised = _normalise_field_policy_key(prefixless)
    if key in PDF_HIDDEN_DIRECT_FIELDS:
        return True
    if _is_hidden_export_field(key, prefixless):
        return True
    if normalised in RO_CRATE_HIDDEN_FIELD_KEYS:
        return True
    if prefixless_normalised in RO_CRATE_HIDDEN_FIELD_KEYS:
        return True
    if any(pattern.search(key) for pattern in PDF_HIDDEN_FIELD_PATTERNS):
        return True
    return bool(
        re.search(r"(^|_)id$", prefixless, re.I)
        and prefixless not in PDF_VISIBLE_ID_FIELDS
        and prefixless_normalised not in PDF_NORMALISED_VISIBLE_ID_FIELDS
    )


class ROCrateTextPDF(FPDF):
    def __init__(self, title, footer_context):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=14)
        self.set_margins(12, 10, 12)
        self.title = title
        self.footer_context = footer_context
        self.font_family = "Helvetica"
        self.unicode_font = False
        self._configure_fonts()

    def _configure_fonts(self):
        font_candidates = [
            (
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
            ),
            (
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ),
        ]
        for regular_path, bold_path in font_candidates:
            if os.path.exists(regular_path) and os.path.exists(bold_path):
                self.add_font("ParkourPDF", "", regular_path)
                self.add_font("ParkourPDF", "B", bold_path)
                self.font_family = "ParkourPDF"
                self.unicode_font = True
                return

    def safe_text(self, value):
        text = str(value if value is not None else "")
        if self.unicode_font:
            return text
        return text.encode("latin-1", "replace").decode("latin-1")

    def footer(self):
        self.set_y(-11)
        self.set_font(self.font_family, "", 7)
        self.set_text_color(90, 110, 120)
        context = self.safe_text(self.footer_context[:118])
        self.cell(0, 6, f"{context} | Page {self.page_no()} of {{nb}}", align="R")
        self.set_text_color(16, 36, 47)


class ROCratePdfRenderer:
    def __init__(self, ro_crate_payload, archive_name, skipped_records=None):
        self.ro_crate = ro_crate_payload or {}
        self.archive_name = archive_name
        self.skipped_records = skipped_records or []
        self.graph = self.ro_crate.get("@graph", [])
        self.entity_map = {
            entity.get(PDF_FIELD_ID): entity
            for entity in self.graph
            if isinstance(entity, dict) and entity.get(PDF_FIELD_ID)
        }
        self.backlink_map = self._build_backlink_map()
        self._request_groups = None
        self._written_record_section_signatures = set()
        self.pdf = None

    def render(self):
        request_groups = self.request_groups()
        footer_context = self._footer_context(request_groups)
        title = self.archive_name.replace(".zip", "").replace("_", " ")
        self.pdf = ROCrateTextPDF(title=title, footer_context=footer_context)
        self.pdf.alias_nb_pages()
        self.pdf.add_page()
        self._write_title(title)
        for request_group in request_groups:
            self._write_request_group(request_group)
        if self.skipped_records:
            self._write_section("Skipped Records")
            self._write_numbered_list(self.skipped_records)
        return bytes(self.pdf.output())

    def _build_backlink_map(self):
        backlink_map = {}
        for entity in self.graph:
            if not isinstance(entity, dict):
                continue
            source_id = entity.get(PDF_FIELD_ID)
            if not source_id:
                continue
            for key, value in entity.items():
                for target_id in self.reference_ids(value):
                    backlink_map.setdefault(target_id, []).append(
                        {"sourceId": source_id, "property": key}
                    )
        return backlink_map

    def _footer_context(self, request_groups):
        request_names = [group["name"] for group in request_groups if group["name"]]
        record_names = [
            record["name"]
            for group in request_groups
            for record in group["records"]
            if record["name"]
        ]
        request_text = (
            f"Request: {request_names[0]}"
            if len(request_names) == 1
            else f"Requests: {', '.join(request_names) or 'Selected requests'}"
        )
        record_text = (
            f"Library/Sample: {record_names[0]}"
            if len(record_names) == 1
            else f"Libraries/Samples: {len(record_names)} selected"
        )
        return f"{request_text} | {record_text}"

    def request_groups(self):
        if self._request_groups is not None:
            return self._request_groups
        studies = [
            entity
            for entity in self.graph
            if str(entity.get(PDF_FIELD_ID, "")).startswith("#study-")
        ]
        groups = [
            self._build_request_group(study, index)
            for index, study in enumerate(studies)
        ]
        groups = [group for group in groups if group["records"] or group["requestRows"]]
        if groups:
            self._request_groups = groups
        else:
            self._request_groups = [self._build_fallback_request_group()]
        return self._request_groups

    def _build_request_group(self, study, index):
        study_id = study.get(PDF_FIELD_ID) or f"request-{index + 1}"
        request_number = self._id_suffix(study_id)
        request_entity = self.entity_by_id(f"#request-context-{request_number}")
        record_ids = self._study_record_ids(study)
        records = sorted(
            [
                record
                for record in (
                    self._build_record(record_id) for record_id in record_ids
                )
                if record
            ],
            key=lambda record: record["name"],
        )
        return {
            "id": study_id,
            "requestNumber": request_number,
            "name": self.entity_label(request_entity)
            or self.entity_label(study)
            or f"Selected request {index + 1}",
            "requestRows": self.rows_for_entity(request_entity, "Request Details"),
            "records": records,
            "attachments": self.attachments_for_request(
                request_entity.get(PDF_FIELD_ID) if request_entity else ""
            ),
        }

    def _build_fallback_request_group(self):
        records = sorted(
            [
                record
                for record in (
                    self._build_record(entity.get(PDF_FIELD_ID))
                    for entity in self.graph
                    if self.is_record_entity(entity)
                )
                if record
            ],
            key=lambda record: record["name"],
        )
        root = self.entity_by_id(RO_CRATE_ROOT_ID)
        return {
            "id": "fallback-request",
            "requestNumber": "",
            "name": self.entity_label(root) or "Selected request",
            "requestRows": self.rows_for_entity(root, "Request Details"),
            "records": records,
            "attachments": self.attachments_for_request(""),
        }

    def _study_record_ids(self, study):
        materials = study.get(PDF_FIELD_MATERIALS) or {}
        ids = [
            *self.reference_ids(materials.get(PDF_FIELD_SAMPLES)),
            *self.reference_ids(materials.get(PDF_FIELD_OTHER_MATERIALS)),
        ]
        ids = [entity_id for entity_id in ids if self.is_record_id(entity_id)]
        if ids:
            return list(dict.fromkeys(ids))
        return [
            entity_id
            for entity_id in self.reference_ids(study.get("hasPart"))
            if self.is_record_id(entity_id)
        ]

    def _build_record(self, record_id):
        entity = self.entity_by_id(record_id)
        if not entity:
            return None
        record_type = self.record_type(entity)
        record_name = (
            entity.get(PDF_FIELD_NAME)
            or entity.get(PDF_FIELD_IDENTIFIER)
            or "Unnamed record"
        )
        sections = {}

        def add_rows(title, rows):
            visible_rows = [row for row in rows if not self.is_hidden_row(row)]
            if visible_rows:
                sections.setdefault(title, []).extend(visible_rows)

        primary_title = f"{record_type}: {record_name}"
        add_rows(
            "Overview",
            [
                {
                    "key": "Name",
                    "value": entity.get(PDF_FIELD_NAME) or "Unnamed record",
                },
                {"key": "Barcode", "value": entity.get(PDF_FIELD_IDENTIFIER) or ""},
            ],
        )
        for row in self.property_rows(entity, skip_summary_models=True):
            add_rows(
                "Overview" if row.get("group") == primary_title else row.get("group"),
                [row],
            )
        for section in self.related_model_sections(entity):
            add_rows(section["title"], section["rows"])
        for section in self.sequencing_sections(entity):
            add_rows(section["title"], section["rows"])
        process_entities = self.record_process_entities(record_id)
        for section in self.process_detail_sections(process_entities):
            add_rows(section["title"], section["rows"])
        add_rows(
            "Processes & Data",
            self.backlink_rows(
                record_id,
                omit_source_ids=[
                    process_entity.get(PDF_FIELD_ID)
                    for process_entity in process_entities
                ],
            ),
        )

        return {
            "id": record_id,
            "type": record_type,
            "name": record_name,
            "barcode": entity.get(PDF_FIELD_IDENTIFIER) or "",
            "sections": [
                {"title": title, "rows": self.unique_rows(rows)}
                for title, rows in sections.items()
                if rows
            ],
        }

    def rows_for_entity(self, entity, default_group):
        if not entity:
            return []
        direct_rows = [
            {
                "key": _pdf_label_for_field(key),
                "value": self.display_value(value),
                "group": default_group,
            }
            for key, value in entity.items()
            if key != PDF_FIELD_NAME and not _pdf_is_hidden_field(key)
        ]
        return [
            row
            for row in [*direct_rows, *self.property_rows(entity)]
            if not self.is_hidden_row(row)
        ]

    def property_rows(self, entity, skip_summary_models=False):
        refs = [
            *self.reference_values(entity.get(PDF_FIELD_ADDITIONAL_PROPERTY)),
            *self.reference_values(entity.get(PDF_FIELD_PARAMETER_VALUE)),
        ]
        properties = [
            prop
            for prop in (self.resolve_reference(ref) for ref in refs)
            if isinstance(prop, dict)
        ]
        property_by_name = {
            prop.get(PDF_FIELD_NAME): prop
            for prop in properties
            if prop.get(PDF_FIELD_NAME)
        }
        rows = []
        for prop in properties:
            name = prop.get(PDF_FIELD_NAME)
            if not name:
                continue
            if skip_summary_models and self.is_summary_model_property(name):
                continue
            if self.is_standalone_measuring_unit_property(name, property_by_name):
                continue
            if self.duplicates_direct_entity_field(
                entity, name, prop.get(PDF_FIELD_VALUE)
            ):
                continue
            row = {
                "key": _pdf_label_for_field(name),
                "value": self.display_property_value(prop, property_by_name),
                "group": self.group_for_property(name, entity),
            }
            if not self.is_hidden_row(row) and not self.is_low_value_preview_row(row):
                rows.append(row)
        return rows

    def related_model_sections(self, entity):
        sections = []
        for related_entity in self.related_model_entities(entity):
            options = self.related_model_display_options(related_entity)
            rows = self.rows_for_related_model_entity(related_entity, **options)
            if rows:
                sections.append(
                    {
                        "title": self.model_section_title_for_entity(related_entity),
                        "rows": rows,
                    }
                )
        return sections

    def related_model_display_options(self, entity):
        entity_id = str(entity.get(PDF_FIELD_ID, ""))
        if entity_id.startswith("#library-type-"):
            return {"omit_relation_keys": {"availableProtocols"}}
        if entity_id.startswith("#index-pair-"):
            return {
                "omit_display_keys": {"indexType"},
                "omit_relation_keys": {"indexI7", "indexI5"},
            }
        return {}

    def related_model_entities(self, entity):
        related = []
        for key in PDF_LINKED_MODEL_RELATION_FIELDS:
            related.extend(
                self.entity_by_id(entity_id)
                for entity_id in self.reference_ids(entity.get(key))
            )
        seen = set()
        unique = []
        for related_entity in related:
            if not related_entity or self.is_low_value_backlink(related_entity):
                continue
            entity_id = related_entity.get(PDF_FIELD_ID)
            if entity_id and entity_id not in seen:
                seen.add(entity_id)
                unique.append(related_entity)
        return unique

    def rows_for_related_model_entity(
        self,
        entity,
        omit_direct_keys=None,
        omit_relation_keys=None,
        omit_display_keys=None,
        omit_property_rows=False,
    ):
        omitted_direct = set(omit_direct_keys or set()) | set(
            omit_display_keys or set()
        )
        direct_rows = [
            {"key": _pdf_label_for_field(key), "value": self.display_value(value)}
            for key, value in entity.items()
            if key != PDF_FIELD_NAME
            and key not in PDF_RELATION_LABELS
            and key not in omitted_direct
            and key not in PDF_RELATED_MODEL_HIDDEN_FIELDS
            and not _pdf_is_hidden_field(key)
            and not self.is_summary_model_property(key)
        ]
        relation_rows = self.relation_rows(
            entity, omit_relation_keys=omit_relation_keys
        )
        property_rows = [] if omit_property_rows else self.property_rows(entity, True)
        return [
            row
            for row in [*direct_rows, *property_rows, *relation_rows]
            if not self.is_hidden_row(row) and not self.is_low_value_preview_row(row)
        ]

    def sequencing_sections(self, entity):
        sections = []
        for flowcell_id in self.reference_ids(entity.get("sequencedOn")):
            flowcell = self.entity_by_id(flowcell_id)
            if not flowcell:
                continue
            rows = self.rows_for_flowcell(flowcell)
            if rows:
                sections.append(
                    {
                        "title": f"Flowcell: {self.short_entity_label(flowcell, 'Flowcell')}",
                        "rows": rows,
                    }
                )
        return sections

    def rows_for_flowcell(self, flowcell):
        rows = [
            *self.rows_for_related_model_entity(
                flowcell, omit_relation_keys={"instrument", "hasInstrument", "hasLane"}
            )
        ]
        for sequencer_id in self.reference_ids(flowcell.get("hasInstrument")):
            self.add_nested_entity_rows(
                rows, "Sequencer", self.entity_by_id(sequencer_id)
            )
        lanes = [
            self.entity_by_id(lane_id)
            for lane_id in self.reference_ids(flowcell.get("hasLane"))
        ]
        lanes = [lane for lane in lanes if lane]
        if len(lanes) > 1:
            rows.append(
                {
                    "key": "Lanes",
                    "value": [self.lane_table_row(lane) for lane in lanes],
                }
            )
        else:
            for lane in lanes:
                self.add_nested_entity_rows(rows, "Lane", lane)
        for data_id in self.reference_ids(flowcell.get("hasPart")):
            data_entity = self.entity_by_id(data_id)
            if (
                data_entity
                and not self.is_lane_entity(data_entity)
                and not self.is_generic_flowcell_data_entity(data_entity)
            ):
                self.add_nested_entity_rows(
                    rows,
                    "Flowcell Data",
                    data_entity,
                    omit_direct_keys={"additionalType", "encodingFormat"},
                    omit_relation_keys={"about", "isPartOf"},
                    omit_entity_summary=True,
                )
        return [
            row
            for row in self.unique_rows(rows)
            if not self.is_hidden_row(row) and not self.is_low_value_preview_row(row)
        ]

    def add_nested_entity_rows(
        self,
        rows,
        label,
        entity,
        omit_direct_keys=None,
        omit_relation_keys=None,
        omit_property_rows=False,
        omit_entity_summary=False,
    ):
        if not entity or self.should_skip_nested_entity(label, entity):
            return
        if not omit_entity_summary:
            rows.append({"key": label, "value": self.entity_label(entity)})
        for row in self.rows_for_related_model_entity(
            entity,
            omit_direct_keys=omit_direct_keys,
            omit_relation_keys=omit_relation_keys,
            omit_property_rows=omit_property_rows,
        ):
            if not self.is_low_value_preview_row(row, label):
                rows.append({**row, "key": f"{label} {row['key']}"})

    def lane_table_row(self, lane):
        row = {"Lane": self.entity_label(lane)}
        for item in self.rows_for_related_model_entity(
            lane, omit_direct_keys={"additionalType"}
        ):
            row[item["key"]] = item["value"]
        return row

    def process_detail_sections(self, process_entities):
        sections = []
        for process_entity in process_entities:
            rows = self.rows_for_process_entity(process_entity)
            if rows:
                sections.append(
                    {"title": self.process_section_title(process_entity), "rows": rows}
                )
        return sections

    def record_process_entities(self, record_id):
        process_ids = [
            link["sourceId"]
            for link in self.backlink_map.get(record_id, [])
            if link["property"] in {"object", "result"}
            and self.is_process_entity(self.entity_by_id(link["sourceId"]))
        ]
        return [
            self.entity_by_id(entity_id)
            for entity_id in dict.fromkeys(process_ids)
            if self.entity_by_id(entity_id)
        ]

    def rows_for_process_entity(self, process_entity):
        rows = [
            *self.rows_for_related_model_entity(
                process_entity,
                omit_relation_keys={"executesLabProtocol", "object", "result"},
            )
        ]
        for protocol_id in self.reference_ids(
            process_entity.get("executesLabProtocol")
        ):
            self.add_nested_entity_rows(
                rows, "Protocol", self.entity_by_id(protocol_id)
            )
        for data_id in self.reference_ids(process_entity.get("result")):
            self.add_nested_entity_rows(
                rows,
                "Data Object",
                self.entity_by_id(data_id),
                omit_direct_keys={
                    "additionalType",
                    "encodingFormat",
                    *PDF_REPEATED_DATA_OBJECT_FIELDS,
                },
                omit_relation_keys=PDF_REPEATED_DATA_OBJECT_FIELDS,
                omit_property_rows=True,
                omit_entity_summary=True,
            )
        return [
            row
            for row in self.unique_rows(rows)
            if not self.is_hidden_row(row) and not self.is_low_value_preview_row(row)
        ]

    def relation_rows(self, entity, omit_relation_keys=None):
        omitted = set(omit_relation_keys or set())
        return [
            {
                "key": label,
                "value": self.display_value(entity[key]),
            }
            for key, label in PDF_RELATION_LABELS.items()
            if key not in omitted and entity.get(key)
        ]

    def backlink_rows(self, entity_id, omit_source_ids=None):
        omitted = set(omit_source_ids or [])
        rows = []
        for link in self.backlink_map.get(entity_id, []):
            if link["property"] not in PDF_BACKLINK_PROPERTIES:
                continue
            if link["sourceId"] in omitted:
                continue
            entity = self.entity_by_id(link["sourceId"])
            if not entity or self.is_low_value_backlink(entity):
                continue
            rows.append(
                {
                    "key": _pdf_label_for_field(link["property"]),
                    "value": self.entity_label(entity),
                }
            )
        return rows

    def attachments_for_request(self, request_context_id):
        files = []
        for entity in self.graph:
            if not self.is_attachment_entity(entity):
                continue
            if request_context_id and request_context_id not in self.reference_ids(
                entity.get(PDF_FIELD_REQUEST_CONTEXT)
            ):
                continue
            files.append(
                {
                    "name": entity.get(PDF_FIELD_NAME)
                    or entity.get(PDF_FIELD_CONTENT_URL)
                    or entity.get(PDF_FIELD_ID),
                    "contentUrl": entity.get(PDF_FIELD_CONTENT_URL),
                }
            )
        return files

    def entity_by_id(self, entity_id):
        return self.entity_map.get(entity_id)

    def entity_types(self, entity):
        value = entity.get(PDF_FIELD_TYPE) if entity else None
        if isinstance(value, list):
            return value
        return [value] if value else []

    def entity_label(self, entity):
        if not entity:
            return ""
        return (
            entity.get(PDF_FIELD_NAME)
            or entity.get(PDF_FIELD_IDENTIFIER)
            or entity.get(PDF_FIELD_ID)
            or ""
        )

    def short_entity_label(self, entity, prefix):
        return re.sub(
            rf"^{re.escape(prefix)}\s+", "", self.entity_label(entity), flags=re.I
        )

    def process_section_title(self, process_entity):
        label = self.entity_label(process_entity)
        match = re.match(
            r"^(sample|library|sequencing)\s+metadata\s+capture\s+for\s+(.+)$",
            label,
            flags=re.I,
        )
        if match:
            return f"Process: {match.group(2)}"
        return f"Process: {label}"

    def is_record_entity(self, entity):
        return self.is_record_id(entity.get(PDF_FIELD_ID) if entity else "")

    def is_record_id(self, entity_id):
        entity_id = str(entity_id or "")
        return entity_id.startswith("#library-material-") or entity_id.startswith(
            "#sample-material-"
        )

    def record_type(self, entity):
        entity_id = str(entity.get(PDF_FIELD_ID, ""))
        if entity_id.startswith("#library-material-"):
            return "Library"
        if entity_id.startswith("#sample-material-"):
            return "Sample"
        type_refs = self.reference_ids(entity.get("additionalType"))
        if any("/Library" in type_ref for type_ref in type_refs):
            return "Library"
        if any("/Sample" in type_ref for type_ref in type_refs):
            return "Sample"
        return "Record"

    def is_attachment_entity(self, entity):
        return (
            "MediaObject" in self.entity_types(entity)
            and entity.get(PDF_FIELD_ID) != "ro-crate-metadata.json"
            and RO_CRATE_ROOT_ID in self.reference_ids(entity.get(PDF_FIELD_IS_PART_OF))
        )

    def is_lane_entity(self, entity):
        return str(entity.get(PDF_FIELD_ID, "") if entity else "").startswith("#lane-")

    def is_process_entity(self, entity):
        return "CreateAction" in self.entity_types(entity)

    def is_assay_entity(self, entity):
        entity_id = str(entity.get(PDF_FIELD_ID, "") if entity else "")
        return (
            entity_id.startswith("#flowcell-assay-")
            or entity_id.startswith("#sample-assay-")
            or entity_id.startswith("#library-assay-")
        )

    def is_generic_flowcell_data_entity(self, entity):
        return bool(
            re.match(r"^#flowcell-data-\d+$", str(entity.get(PDF_FIELD_ID, "")))
        )

    def is_low_value_backlink(self, entity):
        entity_id = str(entity.get(PDF_FIELD_ID, "") if entity else "")
        return entity_id.startswith("#study-") or entity_id.startswith(
            "#source-sample-"
        )

    def should_skip_nested_entity(self, label, entity):
        return self.normalized_display_key(label) == "assay" and self.is_assay_entity(
            entity
        )

    def is_low_value_preview_row(self, row, parent_label=""):
        row_key = self.normalized_display_key(row.get("key"))
        parent_key = self.normalized_display_key(parent_label)
        if self.is_raw_property_name_list_row(row):
            return True
        if row_key.startswith("assay"):
            return True
        if parent_key == "dataobject" and row_key in PDF_REPEATED_DATA_OBJECT_KEYS:
            return True
        return False

    def is_raw_property_name_list_row(self, row):
        if not self.normalized_display_key(row.get("key")).endswith("parametervalue"):
            return False
        values = (
            row.get("value")
            if isinstance(row.get("value"), list)
            else [row.get("value")]
        )
        tokens = []
        for value in values:
            if isinstance(value, str):
                tokens.extend(value.split(","))
        tokens = [re.sub(r"^\d+\.\s*", "", token).strip() for token in tokens if token]
        return bool(tokens) and all(
            PDF_PROPERTY_PREFIX_PATTERN.match(token) for token in tokens
        )

    def normalized_display_key(self, value):
        return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())

    def is_summary_model_property(self, name):
        return str(name or "").startswith(PDF_SUMMARY_PROPERTY_PREFIXES)

    def display_property_value(self, property_value, property_by_name):
        value = self.display_value(property_value.get(PDF_FIELD_VALUE))
        unit = self.unit_for_measured_property(property_value, property_by_name)
        if not unit or self.is_empty(value):
            return value
        return f"{value} {unit}"

    def unit_for_measured_property(self, property_value, property_by_name):
        unit_name = self.measuring_unit_property_name(
            property_value.get(PDF_FIELD_NAME)
        )
        if not unit_name:
            return ""
        return self.display_value(
            property_by_name.get(unit_name, {}).get(PDF_FIELD_VALUE)
        )

    def measuring_unit_property_name(self, property_name):
        property_name = str(property_name or "")
        if property_name.endswith("measured_value_facility"):
            return re.sub(
                r"measured_value_facility$",
                "measuring_unit_facility",
                property_name,
            )
        if property_name.endswith("measured_value"):
            return re.sub(r"measured_value$", "measuring_unit", property_name)
        return ""

    def is_standalone_measuring_unit_property(self, property_name, property_by_name):
        property_name = str(property_name or "")
        if property_name.endswith("measuring_unit_facility"):
            return (
                re.sub(
                    r"measuring_unit_facility$",
                    "measured_value_facility",
                    property_name,
                )
                in property_by_name
            )
        if property_name.endswith("measuring_unit"):
            return (
                re.sub(r"measuring_unit$", "measured_value", property_name)
                in property_by_name
            )
        return False

    def duplicates_direct_entity_field(self, entity, property_name, property_value):
        normalized = PDF_PROPERTY_PREFIX_PATTERN.sub("", str(property_name or ""))
        direct_key_map = {
            "name": PDF_FIELD_NAME,
            "description": "description",
            "identifier": PDF_FIELD_IDENTIFIER,
            "barcode": PDF_FIELD_IDENTIFIER,
        }
        direct_key = direct_key_map.get(normalized)
        if not direct_key or direct_key not in entity:
            return False
        return self.display_value(entity.get(direct_key)) == self.display_value(
            property_value
        )

    def group_for_property(self, name, entity):
        model_name = self.model_name_for_property(name)
        if not model_name:
            return "Additional Details"
        return f"{model_name}: {self.entity_label(entity) or 'Record'}"

    def model_name_for_property(self, name):
        property_name = str(name or "")
        for model_name, prefixes in PDF_MODEL_SECTION_RULES:
            if property_name.startswith(prefixes):
                return model_name
        return None

    def model_section_title_for_entity(self, entity):
        first_property = None
        for ref in [
            *self.reference_values(entity.get(PDF_FIELD_ADDITIONAL_PROPERTY)),
            *self.reference_values(entity.get(PDF_FIELD_PARAMETER_VALUE)),
        ]:
            prop = self.resolve_reference(ref)
            if isinstance(prop, dict) and prop.get(PDF_FIELD_NAME):
                first_property = prop.get(PDF_FIELD_NAME)
                break
        model_name = self.model_name_for_property(
            first_property
        ) or self.model_name_for_id(entity.get(PDF_FIELD_ID))
        return (
            f"{model_name or 'Linked Model'}: {self.entity_label(entity) or 'Record'}"
        )

    def model_name_for_id(self, entity_id):
        entity_id = str(entity_id or "")
        for prefix, model_name in PDF_MODEL_ID_RULES:
            if entity_id.startswith(prefix):
                return model_name
        return None

    def reference_values(self, value):
        if isinstance(value, list):
            return value
        return [value] if value else []

    def reference_ids(self, value):
        ids = []
        for entry in self.reference_values(value):
            if isinstance(entry, list):
                ids.extend(self.reference_ids(entry))
            elif isinstance(entry, dict) and entry.get(PDF_FIELD_ID):
                ids.append(str(entry.get(PDF_FIELD_ID)))
        return [entity_id for entity_id in ids if entity_id]

    def resolve_reference(self, value):
        if isinstance(value, dict) and value.get(PDF_FIELD_ID):
            return self.entity_by_id(value.get(PDF_FIELD_ID)) or value
        return value

    def display_value(self, value):
        if isinstance(value, list):
            return [
                entry
                for entry in (self.display_value(entry) for entry in value)
                if not self.is_empty(entry)
            ]
        if isinstance(value, dict):
            if value.get(PDF_FIELD_ID):
                return self.entity_label(
                    self.entity_by_id(value.get(PDF_FIELD_ID)) or value
                )
            return {
                _pdf_label_for_field(key): displayed
                for key, nested in value.items()
                for displayed in [self.display_value(nested)]
                if not self.is_empty(displayed)
            }
        if isinstance(value, str):
            parsed = self.parse_structured_string(value)
            if parsed is not None:
                return self.display_value(parsed)
        if value is None:
            return ""
        return str(value)

    def parse_structured_string(self, value):
        text = str(value or "").strip()
        if not text or text[0] not in {"{", "["}:
            return None
        try:
            parsed = json.loads(text)
        except ValueError:
            return None
        return parsed if isinstance(parsed, (dict, list)) else None

    def is_hidden_row(self, row):
        return (
            self.is_empty(row.get("value"))
            or _pdf_is_hidden_field(row.get("key"))
            or _pdf_is_hidden_field(
                PDF_PROPERTY_PREFIX_PATTERN.sub("", str(row.get("key")))
            )
        )

    def is_empty(self, value):
        return (
            value in ("", None)
            or (isinstance(value, list) and not value)
            or (isinstance(value, dict) and not value)
        )

    def unique_rows(self, rows):
        seen = set()
        unique = []
        for row in rows:
            key = (
                row.get("key"),
                json.dumps(row.get("value"), sort_keys=True, default=str),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
        return unique

    def _id_suffix(self, entity_id):
        match = re.search(r"(\d+)$", str(entity_id or ""))
        return match.group(1) if match else ""

    def _write_title(self, title):
        self.pdf.set_font(self.pdf.font_family, "B", 14)
        self.pdf.cell(
            0, 8, self.pdf.safe_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        self.pdf.set_font(self.pdf.font_family, "", 8)
        self.pdf.set_text_color(90, 110, 120)
        self.pdf.cell(
            0,
            5,
            self.pdf.safe_text("RO-Crate preview generated from Parkour metadata."),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_text_color(16, 36, 47)
        self.pdf.ln(2)

    def _write_request_group(self, request_group):
        self._write_heading(f"Request: {request_group['name']}", level=1)
        if request_group["requestRows"]:
            self._write_section("Request Details")
            self._write_rows(request_group["requestRows"])
        if request_group["attachments"]:
            self._write_section("Attached Files")
            self._write_numbered_list(
                [
                    file.get("name") or file.get("contentUrl")
                    for file in request_group["attachments"]
                ]
            )
        for record in request_group["records"]:
            self._write_record(record)

    def _write_record(self, record):
        title = f"{record['type']}: {record['name']}"
        if record.get("barcode"):
            title = f"{title} ({record['barcode']})"
        self._write_heading(title, level=2)
        for section in record["sections"]:
            if self._record_section_was_written(section):
                continue
            self._write_section(section["title"])
            self._write_rows(section["rows"])

    def _record_section_was_written(self, section):
        if section.get("title") == "Overview":
            return False
        signature = json.dumps(section, sort_keys=True, default=str)
        if signature in self._written_record_section_signatures:
            return True
        self._written_record_section_signatures.add(signature)
        return False

    def _write_heading(self, text, level):
        self.pdf.ln(3 if level == 1 else 2)
        self.pdf.set_font(self.pdf.font_family, "B", 12 if level == 1 else 10)
        self.pdf.multi_cell(0, 6, self.pdf.safe_text(text))
        self.pdf.ln(1)

    def _write_section(self, text):
        self.pdf.set_font(self.pdf.font_family, "B", 8)
        self.pdf.set_text_color(29, 95, 120)
        self.pdf.multi_cell(0, 5, self.pdf.safe_text(text.upper()))
        self.pdf.set_text_color(16, 36, 47)

    def _write_rows(self, rows):
        for row in rows:
            value = row.get("value")
            if (
                isinstance(value, list)
                and value
                and all(isinstance(item, dict) for item in value)
            ):
                self._write_table(row.get("key"), value)
            elif isinstance(value, dict):
                self._write_key_value(row.get("key"), "")
                self._write_rows(
                    [
                        {"key": key, "value": nested_value}
                        for key, nested_value in value.items()
                    ]
                )
            elif isinstance(value, list):
                self._write_key_value(row.get("key"), "")
                self._write_numbered_list(value)
            else:
                self._write_key_value(row.get("key"), value)
        self.pdf.ln(1)

    def _write_key_value(self, key, value):
        key_width = 42
        gap = 4
        value_width = self.pdf.epw - key_width - gap
        self.pdf.set_x(self.pdf.l_margin)
        y = self.pdf.get_y()
        x = self.pdf.l_margin
        if y > self.pdf.page_break_trigger - 12:
            self.pdf.add_page()
            y = self.pdf.get_y()
            self.pdf.set_x(self.pdf.l_margin)
        self.pdf.set_font(self.pdf.font_family, "B", 8)
        self.pdf.multi_cell(key_width, 4.5, self.pdf.safe_text(key), border=0)
        key_height = self.pdf.get_y() - y
        self.pdf.set_xy(x + key_width + gap, y)
        self.pdf.set_font(self.pdf.font_family, "", 9)
        self.pdf.multi_cell(
            value_width,
            4.5,
            self.pdf.safe_text(self._value_text(value)),
            border=0,
        )
        value_height = self.pdf.get_y() - y
        self.pdf.set_y(y + max(key_height, value_height) + 1)
        self.pdf.set_x(self.pdf.l_margin)

    def _write_numbered_list(self, values):
        for index, value in enumerate(values, start=1):
            self.pdf.set_x(self.pdf.l_margin + 6)
            self.pdf.set_font(self.pdf.font_family, "", 8.5)
            self.pdf.multi_cell(
                0, 4.5, self.pdf.safe_text(f"{index}. {self._value_text(value)}")
            )

    def _write_table(self, title, rows):
        self._write_key_value(title, "")
        if not rows:
            return
        columns = list(dict.fromkeys(key for row in rows for key in row.keys()))
        if len(columns) > 6:
            columns = columns[:6]
        table_data = [["#", *columns]]
        for index, row in enumerate(rows, start=1):
            table_data.append(
                [str(index), *[self._value_text(row.get(column)) for column in columns]]
            )
        widths = [8, *[(self.pdf.epw - 8) / max(len(columns), 1)] * len(columns)]
        line_height = 4.2
        for row_index, cells in enumerate(table_data):
            max_lines = max(
                1,
                *[
                    int(
                        self.pdf.get_string_width(self.pdf.safe_text(cell))
                        / max(width - 2, 1)
                    )
                    + 1
                    for cell, width in zip(cells, widths)
                ],
            )
            row_height = max(line_height, max_lines * line_height)
            if self.pdf.get_y() + row_height > self.pdf.page_break_trigger:
                self.pdf.add_page()
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            for cell, width in zip(cells, widths):
                self.pdf.set_font(
                    self.pdf.font_family, "B" if row_index == 0 else "", 7.5
                )
                self.pdf.rect(x, y, width, row_height)
                self.pdf.set_xy(x + 1, y)
                self.pdf.multi_cell(
                    max(width - 2, 1),
                    line_height,
                    self.pdf.safe_text(cell),
                    border=0,
                    max_line_height=line_height,
                )
                x += width
            self.pdf.set_y(y + row_height)
            self.pdf.set_x(self.pdf.l_margin)
        self.pdf.ln(1)
        self.pdf.set_x(self.pdf.l_margin)

    def _value_text(self, value):
        if isinstance(value, dict):
            return "; ".join(
                f"{key}: {self._value_text(nested_value)}"
                for key, nested_value in value.items()
                if not self.is_empty(nested_value)
            )
        if isinstance(value, list):
            return "; ".join(self._value_text(item) for item in value)
        text = str(value or "")
        if re.fullmatch(r"-?\d+\.\d{5,}", text):
            return f"{float(text):.4f}".rstrip("0").rstrip(".")
        return text


def _zip_response(ro_crate_payload, archive_name, file_entries):
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr(
            "ro-crate-metadata.json",
            json.dumps(ro_crate_payload, indent=2, ensure_ascii=False),
        )
        for archive_path, source_path in file_entries:
            try:
                with open(source_path, "rb") as handle:
                    zip_file.writestr(archive_path, handle.read())
            except OSError:
                continue

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{archive_name}"'
    return response


def _pdf_response(result, skipped_records):
    pdf_name = _ro_crate_pdf_name(result.archive_name)
    pdf_bytes = ROCratePdfRenderer(
        result.ro_crate,
        result.archive_name,
        skipped_records=skipped_records,
    ).render()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{pdf_name}"'
    response["Cache-Control"] = "no-store"
    return response


def _crate_response(preview_requested, pdf_requested, result, skipped_records):
    if pdf_requested:
        return _pdf_response(result, skipped_records)
    if preview_requested:
        response = Response(
            {
                "archive_name": result.archive_name,
                "ro_crate": result.ro_crate,
                "skipped_records": skipped_records,
            }
        )
        response["Cache-Control"] = "no-store"
        return response
    return _zip_response(result.ro_crate, result.archive_name, result.file_entries)


class GenerateROCrate(viewsets.ViewSet):
    def list(self, request):
        selection = _select_records(request)
        if isinstance(selection, Response):
            return selection

        builder = SimpleROCrateBuilder(request, selection)
        result = builder.build()
        return _crate_response(
            selection.preview_requested,
            selection.pdf_requested,
            result,
            selection.skipped_records,
        )


__all__ = ["GenerateROCrate"]
