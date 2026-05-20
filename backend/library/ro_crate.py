import json
import mimetypes
import os
import re
import uuid
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from itertools import chain

from django.apps import apps
from django.conf import settings
from django.db.models import Q, Prefetch
from django.db.models.fields.files import FieldFile
from django.http import HttpResponse
from django.utils import timezone
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
Lane = apps.get_model("flowcell", "Lane")
IndexPool = apps.get_model("index_generator", "Pool")

RO_CRATE_VERSION = "1.2"
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
ISA_INSTRUMENT_URI = f"{ISA_NAMESPACE_URI}Instrument"
ISA_POOL_URI = f"{ISA_NAMESPACE_URI}Pool"
ISA_LANE_URI = f"{ISA_NAMESPACE_URI}Lane"
BIOSCHEMAS_SAMPLE_URI = "https://bioschemas.org/Sample"
BIOSCHEMAS_LAB_PROTOCOL_URI = "https://bioschemas.org/LabProtocol"
BIOSCHEMAS_LAB_PROCESS_URI = "https://bioschemas.org/LabProcess"
PARKOUR_ORGANIZATION_ID = "#parkour-organization"
RO_CRATE_LICENSE_ID = "#parkour-ro-crate-license"
RO_CRATE_LICENSE_NAME = "Parkour metadata export terms"
RO_CRATE_LICENSE_DESCRIPTION = (
    "This RO-Crate is generated from Parkour and reflects the request metadata "
    "available to the exporting user at the time of export. Reuse of the "
    "metadata and any linked underlying data remains subject to the access "
    "controls, policies, and agreements of the originating Parkour system and "
    "the contributing organizations."
)
PARKOUR_SOFTWARE_ID = "#parkour-software"
RO_CRATE_EXPORT_ACTION_ID = "#ro-crate-export-action"
# Parkour status 6 is "Delivered"; earlier statuses are transient and negative
# statuses are failed/compromised states that must not be exported as final RO-Crate records.
RO_CRATE_COMPLETED_STATUS = 6
RO_CRATE_ARCHIVE_STUB_MAX_LENGTH = 180


def _normalise_field_policy_key(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _load_shared_hidden_fields():
    policy_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "shared",
            "roCrateHiddenFields.json",
        )
    )
    try:
        with open(policy_path, encoding="utf-8") as handle:
            policy = json.load(handle)
    except (OSError, ValueError):
        return set()

    return {
        _normalise_field_policy_key(field)
        for field in policy.get("userDefinedVariableHiddenFields", [])
        if field
    }


# Shared with frontend/src/constants/roCratePreviewConsts.js through
# shared/roCrateHiddenFields.json. Keep export exclusions there so preview
# hiding and backend metadata generation do not drift apart.
RO_CRATE_HIDDEN_FIELD_KEYS = _load_shared_hidden_fields()


def _is_hidden_export_field(*field_names):
    return any(
        _normalise_field_policy_key(field_name) in RO_CRATE_HIDDEN_FIELD_KEYS
        for field_name in field_names
        if field_name
    )


@dataclass
class ROCrateExportSelection:
    barcode_values: list
    request_values: list
    selected_sections: set
    accessible_requests: object
    library_data: list
    sample_data: list
    missing_barcodes: list
    missing_requests: list
    non_completed_records: list
    target_request_ids: list


class ROCrateExportSelectionBuilder:
    def __init__(self, request):
        self.request = request

    def build(self):
        barcode_values = _parse_csv_values(self.request.query_params.get("barcodes"))
        request_values = _parse_csv_values(self.request.query_params.get("requests"))
        selected_sections = _normalise_selected_sections(
            self.request.query_params.get("sections")
        )

        if not barcode_values and not request_values:
            return Response(
                {
                    "error": "Provide at least one comma separated barcode value or request name via the 'barcodes' or 'requests' query parameters."
                },
                status=400,
            )

        accessible_requests = get_accessible_requests(self.request)
        accessible_request_ids = list(accessible_requests.values_list("id", flat=True))

        library_data_qs = CompleteLibraryData.objects.filter(
            request_id__in=accessible_request_ids
        )
        sample_data_qs = CompleteSampleData.objects.filter(
            request_id__in=accessible_request_ids
        )

        filters = Q()
        if barcode_values:
            filters |= Q(barcode__in=barcode_values)
        if request_values:
            filters |= Q(request_name__in=request_values)

        if filters:
            library_data_qs = library_data_qs.filter(filters)
            sample_data_qs = sample_data_qs.filter(filters)

        library_data = list(library_data_qs)
        sample_data = list(sample_data_qs)
        found_barcodes = {entry.barcode for entry in chain(library_data, sample_data)}
        missing_barcodes = sorted(
            {barcode for barcode in barcode_values if barcode not in found_barcodes}
        )

        library_data, skipped_libraries = _split_completed_records(library_data)
        sample_data, skipped_samples = _split_completed_records(sample_data)
        non_completed_records = sorted(set(skipped_libraries + skipped_samples))

        if non_completed_records and not library_data and not sample_data:
            return Response(
                {
                    "error": "RO-Crate export requires selected libraries or samples to have Delivered status.",
                    "skipped_records": non_completed_records,
                },
                status=400,
            )

        request_ids_from_data = {
            entry.request_id for entry in chain(library_data, sample_data)
        }

        requests_from_names_qs = accessible_requests.filter(name__in=request_values)
        request_ids_from_names = set(
            requests_from_names_qs.values_list("id", flat=True)
        )
        found_request_names = set(requests_from_names_qs.values_list("name", flat=True))
        missing_requests = sorted(
            {name for name in request_values if name not in found_request_names}
        )
        target_request_ids = sorted(request_ids_from_data.union(request_ids_from_names))

        return ROCrateExportSelection(
            barcode_values=barcode_values,
            request_values=request_values,
            selected_sections=selected_sections,
            accessible_requests=accessible_requests,
            library_data=library_data,
            sample_data=sample_data,
            missing_barcodes=missing_barcodes,
            missing_requests=missing_requests,
            non_completed_records=non_completed_records,
            target_request_ids=target_request_ids,
        )


def _parkour_identifier(entity_type, value):
    if value in (None, ""):
        return None
    return f"urn:parkour:{entity_type}:{value}"


def _guess_encoding_format(filename):
    if not filename:
        return "application/octet-stream"
    guessed_type, _ = mimetypes.guess_type(filename)
    return guessed_type or "application/octet-stream"


def _safe_archive_component(value, fallback):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "")).strip("._")
    return cleaned or fallback


def _archive_stub_for_requests(requests_by_id, target_request_ids):
    request_names = [
        requests_by_id[request_id].name or f"request_{request_id}"
        for request_id in target_request_ids
        if request_id in requests_by_id
    ]
    if not request_names:
        return "parkour"
    archive_stub = "_".join(
        _safe_archive_component(name, f"request_{index + 1}")
        for index, name in enumerate(request_names)
    )
    return archive_stub[:RO_CRATE_ARCHIVE_STUB_MAX_LENGTH].rstrip("._-") or "parkour"


def _is_completed_record(entry):
    return getattr(entry, "status", None) == RO_CRATE_COMPLETED_STATUS


def _record_display_identifier(entry):
    return getattr(entry, "barcode", None) or getattr(entry, "name", None) or str(entry)


def _split_completed_records(records):
    completed_records = []
    skipped_records = []
    for entry in records:
        if _is_completed_record(entry):
            completed_records.append(entry)
        else:
            skipped_records.append(_record_display_identifier(entry))
    return completed_records, skipped_records


def _build_request_file_archive_path(file_obj):
    original_name = getattr(getattr(file_obj, "file", None), "name", None)
    base_name = os.path.basename(original_name or file_obj.name or "")
    safe_name = _safe_archive_component(base_name, f"request_file_{file_obj.id}")
    return f"request-files/{file_obj.id}_{safe_name}"


def _parse_csv_values(raw_value):
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _normalise_property_value(value):
    if value is None:
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
        normalised = []
        for item in value:
            if item in (None, "", []):
                continue
            norm_item = _normalise_property_value(item)
            if norm_item in (None, "", [], {}):
                continue
            normalised.append(norm_item)
        if not normalised:
            return None
        primitive_types = (str, int, float, bool, dict)
        if all(isinstance(item, primitive_types) for item in normalised):
            return normalised
        try:
            return json.dumps(normalised, sort_keys=True, default=str)
        except TypeError:
            return ", ".join(str(item) for item in normalised)
    if isinstance(value, dict):
        safe_dict = {}
        for key, val in value.items():
            if val in (None, "", []):
                continue
            norm_val = _normalise_property_value(val)
            if norm_val in (None, "", [], {}):
                continue
            safe_dict[key] = norm_val
        if not safe_dict:
            return None
        if "@id" in safe_dict:
            return safe_dict
        return json.dumps(safe_dict, sort_keys=True, default=str)
    return value


PATH_REFERENCE_VALUE_KEYS = (
    "path",
    "filepath",
    "file_path",
    "contentUrl",
    "url",
    "value",
)
PATH_REFERENCE_MD5_KEYS = (
    "md5",
    "MD5",
    "md5_hash",
    "md5Hash",
    "checksum_md5",
    "checksumMd5",
)


def _first_mapping_value(mapping, keys):
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _normalise_path_metadata_value(value):
    """Keep path metadata lightweight; never read or hash referenced files here."""
    if value in (None, "", [], {}):
        return None

    if isinstance(value, dict):
        path_value = _first_mapping_value(value, PATH_REFERENCE_VALUE_KEYS)
        md5_value = _first_mapping_value(value, PATH_REFERENCE_MD5_KEYS)
        checksum_value = value.get("checksum")
        if isinstance(checksum_value, dict):
            md5_value = md5_value or _first_mapping_value(
                checksum_value, PATH_REFERENCE_MD5_KEYS
            )

        if path_value is not None or md5_value is not None:
            normalised = {}
            if path_value is not None:
                normalised["path"] = _normalise_property_value(path_value)
            if md5_value is not None:
                normalised["md5"] = _normalise_property_value(md5_value)

            skipped_keys = set(PATH_REFERENCE_VALUE_KEYS).union(
                PATH_REFERENCE_MD5_KEYS,
                {"checksum"},
            )
            for key, nested_value in value.items():
                if key in skipped_keys:
                    continue
                normalised_value = _normalise_path_metadata_value(nested_value)
                if normalised_value not in (None, "", [], {}):
                    normalised[key] = normalised_value
            return normalised or None

        normalised = {}
        for key, nested_value in value.items():
            normalised_value = _normalise_path_metadata_value(nested_value)
            if normalised_value not in (None, "", [], {}):
                normalised[key] = normalised_value
        return normalised or None

    if isinstance(value, (list, tuple, set)):
        normalised = [
            normalised_value
            for normalised_value in (
                _normalise_path_metadata_value(item) for item in value
            )
            if normalised_value not in (None, "", [], {})
        ]
        return normalised or None

    return _normalise_property_value(value)


def _extract_model_fields(instance, prefix=""):
    if instance is None:
        return {}
    data = {}
    for field in instance._meta.concrete_fields:
        field_name = field.name
        if field_name == "archived":
            continue
        exported_field_name = (
            field_name[len("removed_") :] if field_name.startswith("removed_") else field_name
        )
        try:
            value = field.value_from_object(instance)
        except Exception:  # pragma: no cover - defensive
            continue
        target_key = f"{prefix}{exported_field_name}"
        if _is_hidden_export_field(field_name, exported_field_name, target_key):
            continue
        if target_key in data:
            continue
        data[target_key] = value
    return data


def _request_deep_seq_name(request_obj):
    deep_seq_request = getattr(request_obj, "deep_seq_request", None)
    return deep_seq_request.name if deep_seq_request else None


def _extract_request_metadata(request_obj):
    request_data = _extract_model_fields(request_obj, prefix="request_")
    # Request file path JSON may include optional MD5 values supplied by external
    # systems. RO-Crate records that metadata only; it does not read or package
    # the referenced sequencing files because they can be very large.
    for source_field, target_key in (
        ("filepaths", "request_filepaths"),
        ("metapaths", "request_metapaths"),
    ):
        if _is_hidden_export_field(source_field, target_key):
            continue
        normalised_paths = _normalise_path_metadata_value(
            getattr(request_obj, source_field, None)
        )
        if normalised_paths not in (None, "", [], {}):
            request_data[target_key] = normalised_paths
    request_data.update(
        {"request_deep_seq_request": _request_deep_seq_name(request_obj)}
    )
    return request_data


def _build_request_context_entity(request_obj):
    request_context_data = _extract_request_metadata(request_obj)
    return {
        "@id": f"#request-context-{request_obj.id}",
        "@type": "Dataset",
        "name": request_obj.name or f"Request {request_obj.id}",
        "identifier": _parkour_identifier("request", request_obj.id),
        "description": request_obj.description or "",
        "dateCreated": _normalise_property_value(
            getattr(request_obj, "create_time", None)
        ),
        "comments": _deduplicate_comments(_build_comments(request_context_data)),
    }


def _normalise_comment_value(value):
    normalised = _normalise_property_value(value)
    if normalised in (None, "", [], {}):
        return None
    if isinstance(normalised, str):
        return normalised
    if isinstance(normalised, (int, float, bool)):
        return str(normalised)
    try:
        return json.dumps(normalised, sort_keys=True, default=str)
    except TypeError:
        return str(normalised)


def _build_comments(data):
    comments = []
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        comment_value = _normalise_comment_value(value)
        if comment_value in (None, ""):
            continue
        comments.append({"name": key, "value": comment_value})
    return comments


def _append_comment(comments, name, value):
    comment_value = _normalise_comment_value(value)
    if comment_value in (None, ""):
        return
    comments.append({"name": name, "value": comment_value})


def _append_property(properties, name, value):
    normalised = _normalise_property_value(value)
    if normalised in (None, "", [], {}):
        return
    properties.append(
        {
            "@type": "PropertyValue",
            "name": name,
            "value": normalised,
        }
    )


def _deduplicate_properties(properties):
    deduped = []
    seen = set()
    for prop in properties:
        name = prop.get("name")
        value = prop.get("value")
        try:
            value_key = json.dumps(value, sort_keys=True, default=str)
        except TypeError:
            value_key = str(value)
        key = (name, value_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(prop)
    return deduped


def _deduplicate_comments(comments):
    deduped = []
    seen = set()
    for comment in comments:
        key = (comment.get("name"), comment.get("value"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(comment)
    return deduped


def _deduplicate_ref_list(refs):
    deduped = []
    seen = set()
    for ref in refs or []:
        ref_id = ref.get("@id") if isinstance(ref, dict) else None
        if not ref_id or ref_id in seen:
            continue
        seen.add(ref_id)
        deduped.append({"@id": ref_id})
    return deduped


def _ontology_annotation(value):
    if value in (None, ""):
        return None
    return {"annotationValue": str(value)}


def _apply_additional_types(entity, *type_uris):
    refs = [{"@id": type_uri} for type_uri in type_uris if type_uri]
    if not refs:
        return
    entity["additionalType"] = refs[0] if len(refs) == 1 else refs


def _additional_type_ids(entity):
    values = entity.get("additionalType")
    if isinstance(values, dict):
        values = [values]
    if not isinstance(values, list):
        return set()
    return {
        value.get("@id")
        for value in values
        if isinstance(value, dict) and value.get("@id")
    }


def _set_additional_type_ids(entity, *type_uris):
    refs = [{"@id": type_uri} for type_uri in type_uris if type_uri]
    if not refs:
        entity.pop("additionalType", None)
        return
    entity["additionalType"] = refs[0] if len(refs) == 1 else refs


def _set_ref_property(entity, key, refs):
    deduped_refs = _deduplicate_ref_list(refs)
    if not deduped_refs:
        entity.pop(key, None)
        return
    entity[key] = deduped_refs[0] if len(deduped_refs) == 1 else deduped_refs


def _merge_ref_property(entity, key, refs):
    existing = entity.get(key)
    existing_refs = []
    if isinstance(existing, dict):
        existing_refs = [existing]
    elif isinstance(existing, list):
        existing_refs = existing
    deduped_refs = _deduplicate_ref_list(existing_refs + (refs or []))
    if not deduped_refs:
        entity.pop(key, None)
        return
    entity[key] = deduped_refs


def _annotation_to_schema_value(value):
    if isinstance(value, dict):
        if value.get("annotationValue"):
            return value.get("annotationValue")
        if value.get("name"):
            return value.get("name")
    return value


def _format_comment_string(comment):
    name = str(comment.get("name") or "").replace('"', '\\"')
    value = str(comment.get("value") or "").replace('"', '\\"')
    return f'Comment {{Name = "{name}", Value = "{value}"}}'


def _comment_strings(comments):
    return [_format_comment_string(comment) for comment in comments or [] if comment]


def _comments_to_additional_properties(comments, value_type=None):
    properties = []
    for comment in comments or []:
        name = comment.get("name")
        value = _normalise_property_value(comment.get("value"))
        if name in (None, "") or value in (None, "", [], {}):
            continue
        entry = {
            "@type": "PropertyValue",
            "name": name,
            "value": value,
        }
        if value_type:
            entry["additionalType"] = value_type
        properties.append(entry)
    return _deduplicate_properties(properties)


def _merge_property_values(entity, property_name, property_values):
    existing = entity.get(property_name, [])
    if isinstance(existing, dict):
        existing = [existing]
    merged = _deduplicate_properties((existing or []) + (property_values or []))
    if merged:
        entity[property_name] = merged
    else:
        entity.pop(property_name, None)


def _move_comments_to_additional_properties(entity, value_type=None):
    comments = entity.pop("comments", [])
    if not comments:
        return
    _merge_property_values(
        entity,
        "additionalProperty",
        _comments_to_additional_properties(comments, value_type=value_type),
    )


def _align_to_nfdi4plants_profile(ro_crate):
    graph = ro_crate.get("@graph", [])
    profile_present = any(
        entity.get("@id") == NFDI4PLANTS_ISA_PROFILE_URI for entity in graph
    )
    if not profile_present:
        graph.append(
            {
                "@id": NFDI4PLANTS_ISA_PROFILE_URI,
                "@type": "CreativeWork",
                "name": "NFDI4Plants ISA RO-Crate profile",
                "url": NFDI4PLANTS_ISA_PROFILE_URI,
            }
        )

    publisher_present = any(
        entity.get("@id") == PARKOUR_ORGANIZATION_ID for entity in graph
    )
    if not publisher_present:
        graph.append(
            {
                "@id": PARKOUR_ORGANIZATION_ID,
                "@type": "Organization",
                "name": "Parkour",
                "url": "https://github.com/maxplanck-ie/parkour2",
            }
        )

    for entity in graph:
        entity_id = str(entity.get("@id") or "")
        additional_types = _additional_type_ids(entity)

        if entity_id == "./":
            if entity.get("creator") == {"@id": PARKOUR_SOFTWARE_ID}:
                entity["publisher"] = {"@id": PARKOUR_ORGANIZATION_ID}
            creators = entity.pop("people", [])
            if creators:
                _set_ref_property(entity, "creator", creators)
            if entity.get("studies"):
                _merge_ref_property(entity, "hasPart", entity.pop("studies"))
            _move_comments_to_additional_properties(entity)
            continue

        if ISA_STUDY_URI in additional_types:
            creators = entity.pop("people", [])
            if creators:
                _set_ref_property(entity, "creator", creators)
            if entity.get("processSequence"):
                _set_ref_property(entity, "about", entity.pop("processSequence"))
            if entity.get("assays"):
                _merge_ref_property(entity, "hasPart", entity.pop("assays"))
            entity.pop("protocols", None)
            entity.pop("materials", None)
            _move_comments_to_additional_properties(entity)
            continue

        if ISA_ASSAY_URI in additional_types:
            if entity.get("processSequence"):
                _set_ref_property(entity, "about", entity.pop("processSequence"))
            if entity.get("dataFiles"):
                _merge_ref_property(entity, "hasPart", entity.pop("dataFiles"))
            if "measurementType" in entity:
                entity["variableMeasured"] = _annotation_to_schema_value(
                    entity.pop("measurementType")
                )
            if "technologyType" in entity:
                entity["measurementMethod"] = _annotation_to_schema_value(
                    entity.pop("technologyType")
                )
            if "technologyPlatform" in entity:
                entity["measurementTechnique"] = entity.pop("technologyPlatform")
            comments = entity.pop("comments", [])
            if comments:
                entity["comment"] = _comment_strings(comments)
            continue

        if ISA_PROCESS_URI in additional_types:
            _set_additional_type_ids(entity, BIOSCHEMAS_LAB_PROCESS_URI)
            if entity.get("inputs"):
                _set_ref_property(entity, "object", entity.pop("inputs"))
            if entity.get("outputs"):
                _set_ref_property(entity, "result", entity.pop("outputs"))
            if entity.get("executesProtocol"):
                entity["executesLabProtocol"] = entity.pop("executesProtocol")
            comments = entity.pop("comments", [])
            if comments:
                entity["disambiguatingDescription"] = "\n".join(
                    _comment_strings(comments)
                )
                _merge_property_values(
                    entity,
                    "parameterValue",
                    _comments_to_additional_properties(
                        comments, value_type="ParameterValue"
                    ),
                )
            continue

        if ISA_PROTOCOL_URI in additional_types:
            entity["@type"] = "HowTo"
            _set_additional_type_ids(entity, BIOSCHEMAS_LAB_PROTOCOL_URI)
            _move_comments_to_additional_properties(entity)
            continue

        if entity_id.startswith("#sample-material-") or entity_id.startswith(
            "#source-sample-"
        ):
            _set_additional_type_ids(entity, BIOSCHEMAS_SAMPLE_URI)
            _move_comments_to_additional_properties(
                entity, value_type="CharacteristicValue"
            )
            continue

        if ISA_DATA_URI in additional_types:
            entity["@type"] = "MediaObject"
            entity.setdefault("encodingFormat", "application/json")
            _move_comments_to_additional_properties(entity)
            continue

        if entity.get("@type") == "Person":
            comments = entity.pop("comments", [])
            remaining_comments = []
            for comment in comments:
                if comment.get("name") == "user_phone" and comment.get("value"):
                    entity["telephone"] = comment.get("value")
                else:
                    remaining_comments.append(comment)
            if "affiliatedOrganization" in entity:
                entity["affiliation"] = entity.pop("affiliatedOrganization")
            if remaining_comments:
                _merge_property_values(
                    entity,
                    "additionalProperty",
                    _comments_to_additional_properties(remaining_comments),
                )
            continue

        if "affiliatedOrganization" in entity and entity.get("@type") == "Organization":
            entity["affiliation"] = entity.pop("affiliatedOrganization")

        _move_comments_to_additional_properties(entity)

    ro_crate["@graph"] = graph
    return ro_crate


RO_CRATE_SECTION_IDS = {
    "request",
    "request_user",
    "organizations",
    "principal_investigators",
    "cost_units",
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


def _normalise_selected_sections(raw_sections):
    requested_sections = _parse_csv_values(raw_sections)
    if not requested_sections:
        return set(RO_CRATE_SECTION_IDS)
    selected_sections = {
        section for section in requested_sections if section in RO_CRATE_SECTION_IDS
    }
    return selected_sections or set(RO_CRATE_SECTION_IDS)


def _entity_section(entity):
    entity_id = str(entity.get("@id") or "")
    if entity_id in {"ro-crate-metadata.json", "./"}:
        return None
    if entity_id.startswith("#person-"):
        return "request_user"
    if entity_id.startswith("#organization-"):
        return "organizations"
    if entity_id.startswith("#principal-investigator-"):
        return "principal_investigators"
    if entity_id.startswith("#cost-unit-"):
        return "cost_units"
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
    if entity_id.startswith("#nucleic-acid-type-"):
        return "nucleic_acid_types"
    if entity_id.startswith("#index-pool-"):
        return "index_pools"
    if entity_id.startswith("#sequencer-"):
        return "sequencers"
    if entity_id.startswith("#lane-"):
        return "lanes"
    if entity_id.startswith("#request-file-"):
        return "request"
    if entity_id.startswith("#request-context-"):
        return "request"
    if (
        entity_id.startswith("#source-sample-")
        or entity_id.startswith("#sample-process-")
        or entity_id.startswith("#sample-data-")
    ):
        return "samples"
    if entity_id.startswith("#library-process-") or entity_id.startswith(
        "#library-data-"
    ):
        return "libraries"
    if entity_id.startswith("#flowcell-process-") or entity_id.startswith(
        "#flowcell-data-"
    ):
        return "flowcells"
    if entity_id.startswith("#sample-material-"):
        return "samples"
    if entity_id.startswith("#library-material-") or entity_id.startswith(
        "#library-assay-"
    ):
        return "libraries"
    if entity_id.startswith("#flowcell-assay-"):
        return "flowcells"
    return None


def _property_section(entity_id, property_name):
    entity_id = str(entity_id or "")
    property_name = str(property_name or "")

    if entity_id == "./":
        if property_name.startswith("request_"):
            return "request"
        if property_name == "costUnit":
            return "cost_units"
        if property_name == "affiliatedOrganization":
            return "organizations"
        if property_name == "principalInvestigator":
            return "principal_investigators"
        return None

    if entity_id.startswith("#study-"):
        if property_name == "study_request_identifier":
            return "request"
        if property_name == "study_samples_count":
            return "samples"
        if property_name == "study_libraries_count":
            return "libraries"
        if property_name == "flowcell_assays":
            return "flowcells"
        return None

    if entity_id.startswith("#person-"):
        if property_name.startswith("user_"):
            return "request_user"
        if property_name == "affiliatedOrganization":
            return "organizations"
        if property_name == "principalInvestigator":
            return "principal_investigators"
        return None

    if entity_id.startswith("#principal-investigator-"):
        if property_name.startswith("principal_investigator_"):
            return "principal_investigators"
        if property_name == "affiliatedOrganization":
            return "organizations"
        return None

    if entity_id.startswith("#cost-unit-"):
        if property_name.startswith("cost_unit_"):
            return "cost_units"
        if property_name == "principalInvestigator":
            return "principal_investigators"
        return None

    if entity_id.startswith("#protocol-") and property_name.startswith("protocol_"):
        return "protocols"
    if entity_id.startswith("#organism-") and property_name.startswith("organism_"):
        return "organisms"
    if entity_id.startswith("#library-type-") and property_name.startswith(
        "library_type_"
    ):
        return "library_types"
    if entity_id.startswith("#read-length-") and property_name.startswith(
        "read_length_"
    ):
        return "read_lengths"
    if entity_id.startswith("#index-type-") and property_name.startswith("index_type_"):
        return "index_types"
    if entity_id.startswith("#nucleic-acid-type-") and property_name.startswith(
        "nucleic_acid_type_"
    ):
        return "nucleic_acid_types"
    if entity_id.startswith("#index-pool-") and property_name.startswith("index_pool_"):
        return "index_pools"
    if entity_id.startswith("#sequencer-") and property_name.startswith("sequencer_"):
        return "sequencers"

    if entity_id.startswith("#lane-"):
        if property_name.startswith("lane_"):
            return "lanes"
        if property_name == "associatedPool":
            return "index_pools"
        return None

    if entity_id.startswith("#request-file-"):
        if property_name.startswith("request_file_"):
            return "request"
        return None

    if entity_id.startswith("#request-context-"):
        if property_name.startswith("request_"):
            return "request"
        return None

    if entity_id.startswith("#sample-material-"):
        if property_name.startswith("sample_db_") or property_name.startswith(
            "sample_mv_"
        ):
            return "samples"
        if property_name.startswith("library_preparation_"):
            return "library_preparation"
        if property_name.startswith("pooling_"):
            return "pooling"
        if property_name == "associatedPool":
            return "index_pools"
        return None

    if entity_id.startswith("#library-material-"):
        if property_name.startswith("library_db_"):
            return "libraries"
        if property_name.startswith("pooling_"):
            return "pooling"
        if property_name == "associatedPool":
            return "index_pools"
        return None

    if entity_id.startswith("#library-assay-") and property_name.startswith(
        "library_mv_"
    ):
        return "libraries"

    if entity_id.startswith("#flowcell-assay-"):
        if property_name.startswith("flowcell_"):
            return "flowcells"
        return None

    return None


def _filter_internal_refs(value, kept_ids):
    if isinstance(value, list):
        filtered = []
        for item in value:
            filtered_item = _filter_internal_refs(item, kept_ids)
            if filtered_item in (None, {}):
                continue
            filtered.append(filtered_item)
        return filtered

    if isinstance(value, dict):
        ref_id = value.get("@id")
        if ref_id and str(ref_id).startswith("#") and ref_id not in kept_ids:
            return None
        filtered_dict = {}
        for key, nested_value in value.items():
            filtered_value = _filter_internal_refs(nested_value, kept_ids)
            if filtered_value is None:
                continue
            filtered_dict[key] = filtered_value
        return filtered_dict

    return value


def _filter_additional_properties(entity, selected_sections, kept_ids):
    entity_id = entity.get("@id")
    filtered_properties = []
    for prop in entity.get("additionalProperty", []):
        section = _property_section(entity_id, prop.get("name"))
        if section and section not in selected_sections:
            continue
        filtered_value = _filter_internal_refs(prop.get("value"), kept_ids)
        if filtered_value in (None, "", {}):
            continue
        if isinstance(filtered_value, list) and not filtered_value:
            continue
        filtered_properties.append(
            {
                "@type": prop.get("@type", "PropertyValue"),
                "name": prop.get("name"),
                "value": filtered_value,
            }
        )
    return filtered_properties


def _filter_comments(entity, selected_sections):
    entity_id = entity.get("@id")
    filtered_comments = []
    for comment in entity.get("comments", []):
        section = _property_section(entity_id, comment.get("name"))
        if section and section not in selected_sections:
            continue
        comment_value = _normalise_comment_value(comment.get("value"))
        if comment_value in (None, ""):
            continue
        filtered_comments.append(
            {
                "name": comment.get("name"),
                "value": comment_value,
            }
        )
    return filtered_comments


def _filter_ro_crate_sections(ro_crate, selected_sections):
    graph = ro_crate.get("@graph", [])
    filtered_graph = []

    for entity in graph:
        section = _entity_section(entity)
        if section and section not in selected_sections:
            continue
        filtered_graph.append(dict(entity))

    kept_ids = {
        entity.get("@id")
        for entity in filtered_graph
        if entity.get("@id") not in (None, "")
    }

    sanitised_graph = []
    for entity in filtered_graph:
        cleaned_entity = {}
        for key, value in entity.items():
            if key in {"additionalProperty", "comments"}:
                continue
            filtered_value = _filter_internal_refs(value, kept_ids)
            if filtered_value is None:
                continue
            cleaned_entity[key] = filtered_value

        if "additionalProperty" in entity:
            cleaned_entity["additionalProperty"] = _filter_additional_properties(
                entity, selected_sections, kept_ids
            )
        if "comments" in entity:
            cleaned_entity["comments"] = _filter_comments(entity, selected_sections)

        sanitised_graph.append(cleaned_entity)

    ro_crate["@graph"] = sanitised_graph
    return ro_crate


def _build_ro_crate_zip_response(ro_crate_payload, archive_name, file_entries):
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr(
            "ro-crate-metadata.json",
            json.dumps(ro_crate_payload, indent=2, ensure_ascii=False),
        )

        for archive_path, source_path in file_entries:
            if not archive_path or not source_path:
                continue
            try:
                with open(source_path, "rb") as handle:
                    zip_file.writestr(archive_path, handle.read())
            except OSError:
                continue

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{archive_name}"'
    return response


def _is_preview_response_requested(request):
    return str(request.query_params.get("preview") or "").lower() in {
        "1",
        "true",
        "yes",
    }


def _build_ro_crate_response(
    request, ro_crate_payload, archive_name, file_entries, skipped_records=None
):
    if _is_preview_response_requested(request):
        response = Response(
            {
                "archive_name": archive_name,
                "ro_crate": ro_crate_payload,
                "skipped_records": skipped_records or [],
            }
        )
        response["Cache-Control"] = "no-store"
        return response
    return _build_ro_crate_zip_response(ro_crate_payload, archive_name, file_entries)


def _software_entity():
    return {
        "@id": PARKOUR_SOFTWARE_ID,
        "@type": "SoftwareApplication",
        "name": "Parkour",
        "identifier": _parkour_identifier("software", "parkour2"),
        "softwareVersion": str(getattr(settings, "VERSION", "")) or None,
        "url": "https://github.com/maxplanck-ie/parkour2",
    }


def _metadata_descriptor_entity():
    return {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {"@id": RO_CRATE_SPEC_URI},
        "about": {"@id": "./"},
    }


def _license_entity():
    return {
        "@id": RO_CRATE_LICENSE_ID,
        "@type": "CreativeWork",
        "name": RO_CRATE_LICENSE_NAME,
        "description": RO_CRATE_LICENSE_DESCRIPTION,
    }


def _export_action_entity(timestamp, result="./", object_refs=None, agent_ref=None):
    entity = {
        "@id": RO_CRATE_EXPORT_ACTION_ID,
        "@type": "CreateAction",
        "name": "Parkour RO-Crate export generation",
        "instrument": {"@id": PARKOUR_SOFTWARE_ID},
        "result": {"@id": result},
        "endTime": timestamp,
        "actionStatus": {"@id": "https://schema.org/CompletedActionStatus"},
    }
    if object_refs:
        entity["object"] = _deduplicate_ref_list(object_refs)
    if agent_ref:
        entity["agent"] = {"@id": agent_ref}
    return entity


def _empty_ro_crate_payload(timestamp, published_date):
    return {
        "@context": [
            RO_CRATE_CONTEXT_URI,
            {"@base": "./"},
        ],
        "@graph": [
            _metadata_descriptor_entity(),
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Parkour RO-Crate export",
                "identifier": _parkour_identifier("ro-crate-export", timestamp),
                "dateCreated": timestamp,
                "datePublished": published_date,
                "description": "No matching barcodes or requests were found.",
                "license": {"@id": RO_CRATE_LICENSE_ID},
                "creator": {"@id": PARKOUR_SOFTWARE_ID},
            },
            _software_entity(),
            _license_entity(),
            _export_action_entity(timestamp),
        ],
    }


def _empty_ro_crate_response(request):
    now = timezone.now()
    return _build_ro_crate_response(
        request,
        _empty_ro_crate_payload(now.isoformat(), now.date().isoformat()),
        "parkour_ro_crate.zip",
        [],
        [],
    )


def _selected_requests_by_id(accessible_requests, target_request_ids):
    requests_qs = (
        accessible_requests.filter(id__in=target_request_ids)
        .select_related(
            "user",
            "cost_unit",
            "user__organization",
            "user__pi",
            "user__pi__organization",
            "cost_unit__pi",
            "cost_unit__pi__organization",
        )
        .prefetch_related("files")
    )
    return {req.id: req for req in requests_qs}


class GenerateROCrate(viewsets.ViewSet):
    def list(self, request):
        selection = ROCrateExportSelectionBuilder(request).build()
        if isinstance(selection, Response):
            return selection

        barcode_values = selection.barcode_values
        request_values = selection.request_values
        selected_sections = selection.selected_sections
        accessible_requests = selection.accessible_requests
        library_data = selection.library_data
        sample_data = selection.sample_data
        missing_barcodes = selection.missing_barcodes
        missing_requests = selection.missing_requests
        non_completed_records = selection.non_completed_records

        if not selection.target_request_ids:
            return _empty_ro_crate_response(request)

        target_request_ids = selection.target_request_ids
        single_request_id = target_request_ids[0]
        is_multi_request_export = len(target_request_ids) > 1
        requests_by_id = _selected_requests_by_id(
            accessible_requests, target_request_ids
        )
        root_request = requests_by_id.get(single_request_id)
        if root_request is None:
            return Response(
                {"error": "The selected request is no longer accessible."}, status=404
            )

        organization_entities = {}
        organism_entities = {}
        pi_entities = {}
        cost_unit_entities = {}
        protocol_entities = {}
        library_type_entities = {}
        read_length_entities = {}
        index_type_entities = {}
        nucleic_acid_entities = {}
        index_pool_entities = {}
        sequencer_entities = {}
        lane_entities = {}
        request_file_entities = {}
        request_file_archives = {}
        source_entities = {}
        process_entities = {}
        data_file_entities = {}
        user_entities = {}
        request_context_entities = {}

        def register_organization(organization):
            if organization is None:
                return None
            entity_id = f"#organization-{organization.id}"
            if entity_id not in organization_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(organization, prefix="organization_")
                    )
                )
                organization_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Organization",
                    "name": organization.name or str(organization),
                    "identifier": _parkour_identifier("organization", organization.id),
                    "description": getattr(organization, "comment", None) or None,
                    "comments": comments,
                }
            return entity_id

        def register_principal_investigator(pi_obj):
            if pi_obj is None:
                return None
            entity_id = f"#principal-investigator-{pi_obj.id}"
            if entity_id not in pi_entities:
                comments = _build_comments(
                    _extract_model_fields(pi_obj, prefix="principal_investigator_")
                )
                pi_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Person",
                    "name": pi_obj.name or str(pi_obj),
                    "identifier": _parkour_identifier(
                        "principal-investigator", pi_obj.id
                    ),
                    "comments": _deduplicate_comments(comments),
                }
                if pi_obj.organization:
                    pi_entities[entity_id]["affiliatedOrganization"] = {
                        "@id": f"#organization-{pi_obj.organization.id}"
                    }
            return entity_id

        def register_organism(organism):
            if organism is None:
                return None
            entity_id = f"#organism-{organism.id}"
            if entity_id not in organism_entities:
                comments = _deduplicate_comments(
                    _build_comments(_extract_model_fields(organism, prefix="organism_"))
                )
                organism_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": organism.name or str(organism),
                    "identifier": _parkour_identifier("organism", organism.id),
                    "comments": comments,
                }
                _apply_additional_types(
                    organism_entities[entity_id], ISA_ORGANISM_URI
                )
            return entity_id

        def register_cost_unit(cost_unit):
            if cost_unit is None:
                return None
            entity_id = f"#cost-unit-{cost_unit.id}"
            if entity_id not in cost_unit_entities:
                comments = _build_comments(
                    _extract_model_fields(cost_unit, prefix="cost_unit_")
                )
                cost_unit_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": cost_unit.name or str(cost_unit),
                    "identifier": _parkour_identifier("cost-unit", cost_unit.id),
                    "comments": _deduplicate_comments(comments),
                }
                if cost_unit.pi:
                    cost_unit_entities[entity_id]["principalInvestigator"] = {
                        "@id": f"#principal-investigator-{cost_unit.pi.id}"
                    }
            return entity_id

        def register_protocol(protocol):
            if protocol is None:
                return None
            entity_id = f"#protocol-{protocol.id}"
            if entity_id not in protocol_entities:
                comments = _deduplicate_comments(
                    _build_comments(_extract_model_fields(protocol, prefix="protocol_"))
                )
                protocol_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "CreativeWork",
                    "name": protocol.name or str(protocol),
                    "identifier": _parkour_identifier("protocol", protocol.id),
                    "description": getattr(protocol, "comment", None) or None,
                    "comments": comments,
                }
                _apply_additional_types(
                    protocol_entities[entity_id], ISA_PROTOCOL_URI
                )
            return entity_id

        def register_library_type(library_type):
            if library_type is None:
                return None
            entity_id = f"#library-type-{library_type.id}"
            if entity_id not in library_type_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(library_type, prefix="library_type_")
                    )
                )
                library_type_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": library_type.name or str(library_type),
                    "identifier": _parkour_identifier("library-type", library_type.id),
                    "comments": comments,
                }
                _apply_additional_types(
                    library_type_entities[entity_id], ISA_MATERIAL_URI
                )
            return entity_id

        def register_read_length(read_length):
            if read_length is None:
                return None
            entity_id = f"#read-length-{read_length.id}"
            if entity_id not in read_length_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(read_length, prefix="read_length_")
                    )
                )
                read_length_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": read_length.name or str(read_length),
                    "identifier": _parkour_identifier("read-length", read_length.id),
                    "comments": comments,
                }
            return entity_id

        def register_index_type(index_type):
            if index_type is None:
                return None
            entity_id = f"#index-type-{index_type.id}"
            if entity_id not in index_type_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(index_type, prefix="index_type_")
                    )
                )
                index_type_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": index_type.name or str(index_type),
                    "identifier": _parkour_identifier("index-type", index_type.id),
                    "comments": comments,
                }
            return entity_id

        def register_nucleic_acid(nucleic_acid):
            if nucleic_acid is None:
                return None
            entity_id = f"#nucleic-acid-type-{nucleic_acid.id}"
            if entity_id not in nucleic_acid_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(nucleic_acid, prefix="nucleic_acid_type_")
                    )
                )
                nucleic_acid_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": nucleic_acid.name or str(nucleic_acid),
                    "identifier": _parkour_identifier(
                        "nucleic-acid-type", nucleic_acid.id
                    ),
                    "comments": comments,
                }
                _apply_additional_types(
                    nucleic_acid_entities[entity_id], ISA_MATERIAL_URI
                )
            return entity_id

        def register_index_pool(pool):
            if pool is None:
                return None
            entity_id = f"#index-pool-{pool.id}"
            if entity_id not in index_pool_entities:
                comments = _build_comments(
                    {
                        "index_pool_loaded": pool.loaded,
                        "index_pool_comment": pool.comment,
                    }
                )
                if pool.size:
                    comments.extend(
                        _build_comments(
                            _extract_model_fields(pool.size, prefix="index_pool_size_")
                        )
                    )
                if pool.user:
                    user_name = getattr(pool.user, "full_name", None) or (
                        f"{pool.user.first_name} {pool.user.last_name}".strip()
                        or pool.user.email
                    )
                    _append_comment(comments, "index_pool_user_name", user_name)
                    _append_comment(comments, "index_pool_user_email", pool.user.email)
                index_pool_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": pool.name or f"Pool {pool.id}",
                    "identifier": _parkour_identifier("index-pool", pool.id),
                    "comments": _deduplicate_comments(comments),
                }
                _apply_additional_types(
                    index_pool_entities[entity_id], ISA_POOL_URI
                )
                pool_member_refs = [
                    {"@id": f"#library-material-{library.id}"}
                    for library in pool.libraries.all()
                    if library.id in library_id_set
                ] + [
                    {"@id": f"#sample-material-{sample.id}"}
                    for sample in pool.samples.all()
                    if sample.id in sample_id_set
                ]
                if pool_member_refs:
                    index_pool_entities[entity_id]["member"] = _deduplicate_ref_list(
                        pool_member_refs
                    )
            return entity_id

        def register_sequencer(sequencer):
            if sequencer is None:
                return None
            entity_id = f"#sequencer-{sequencer.id}"
            if entity_id not in sequencer_entities:
                comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(sequencer, prefix="sequencer_")
                    )
                )
                sequencer_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": sequencer.name or str(sequencer),
                    "identifier": _parkour_identifier("sequencer", sequencer.id),
                    "comments": comments,
                }
                _apply_additional_types(
                    sequencer_entities[entity_id], ISA_INSTRUMENT_URI
                )
            return entity_id

        def register_lane(lane):
            if lane is None:
                return None
            entity_id = f"#lane-{lane.id}"
            if entity_id not in lane_entities:
                comments = _build_comments(
                    {
                        "lane_loading_concentration": lane.loading_concentration,
                        "lane_phix": lane.phix,
                        "lane_completed": lane.completed,
                        "lane_name": lane.name,
                    }
                )
                if lane.pool:
                    pool_id = register_index_pool(lane.pool)
                lane_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": lane.name or f"Lane {lane.id}",
                    "identifier": _parkour_identifier("lane", lane.id),
                    "comments": _deduplicate_comments(comments),
                }
                _apply_additional_types(
                    lane_entities[entity_id], ISA_LANE_URI
                )
                if lane.pool and pool_id:
                    lane_entities[entity_id]["associatedPool"] = {"@id": pool_id}
            return entity_id

        def register_user_entity(user_obj):
            if user_obj is None:
                return None
            if user_obj.id in user_entities:
                return user_entities[user_obj.id]["@id"]

            user_comments = _build_comments(
                {
                    "user_email": user_obj.email,
                    "user_phone": user_obj.phone,
                    "user_is_pi": getattr(user_obj, "is_pi", False),
                    "user_is_staff": getattr(user_obj, "is_staff", False),
                }
            )

            entity_id = f"#person-{user_obj.id}"
            user_entities[user_obj.id] = {
                "@id": entity_id,
                "@type": "Person",
                "name": user_obj.full_name,
                "identifier": _parkour_identifier("user", user_obj.id),
                "givenName": user_obj.first_name or None,
                "familyName": user_obj.last_name or None,
                "email": user_obj.email or None,
                "comments": _deduplicate_comments(user_comments),
            }
            if user_obj.organization:
                org_id = register_organization(user_obj.organization)
                if org_id:
                    user_entities[user_obj.id]["affiliatedOrganization"] = {
                        "@id": org_id
                    }
            if user_obj.pi:
                pi_id = register_principal_investigator(user_obj.pi)
                if pi_id:
                    user_entities[user_obj.id]["principalInvestigator"] = {"@id": pi_id}

            return entity_id

        def register_request_file(file_obj, request_obj):
            if file_obj is None:
                return None
            archive_path = _build_request_file_archive_path(file_obj)
            entity_id = archive_path
            if entity_id not in request_file_entities:
                file_field = getattr(file_obj, "file", None)
                file_storage_path = getattr(file_field, "name", None)
                try:
                    file_disk_path = file_field.path if file_field else None
                except Exception:
                    file_disk_path = None
                if not file_disk_path or not os.path.exists(file_disk_path):
                    return None
                request_file_archives[entity_id] = file_disk_path
                request_file_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": ["File", "MediaObject"],
                    "name": file_obj.name
                    or (file_storage_path or f"Request file {file_obj.id}"),
                    "identifier": _parkour_identifier("request-file", file_obj.id),
                    "encodingFormat": _guess_encoding_format(
                        file_storage_path or file_obj.name
                    ),
                    "isPartOf": {"@id": "./"},
                    "about": {"@id": f"#study-{request_obj.id}"},
                    "requestContext": {"@id": f"#request-context-{request_obj.id}"},
                    "comments": _deduplicate_comments(
                        _build_comments(
                            {
                                "request_file_name": file_obj.name,
                                "request_file_storage_path": file_storage_path,
                            }
                        )
                    ),
                }
            return entity_id

        library_ids = [entry.library_id for entry in library_data]
        sample_ids = [entry.sample_id for entry in sample_data]

        libraries_qs = (
            Library.objects.filter(id__in=library_ids)
            .select_related(
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            )
            .prefetch_related("request")
        )
        samples_qs = (
            Sample.objects.filter(id__in=sample_ids)
            .select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            )
            .prefetch_related("request")
        )

        libraries_by_id = {library.id: library for library in libraries_qs}
        samples_by_id = {sample.id: sample for sample in samples_qs}

        library_id_set = set(library_ids)
        sample_id_set = set(sample_ids)

        library_preparations_by_sample = {}
        if sample_ids:
            library_preparations_by_sample = {
                lp.sample_id: lp
                for lp in LibraryPreparation.objects.filter(sample_id__in=sample_ids)
            }

        pooling_by_library = {}
        pooling_by_sample = {}
        if library_ids or sample_ids:
            pooling_qs = Pooling.objects.filter(
                Q(library_id__in=library_ids) | Q(sample_id__in=sample_ids)
            ).select_related("library", "sample")
            for pooling_record in pooling_qs:
                if pooling_record.library_id:
                    pooling_by_library[pooling_record.library_id] = pooling_record
                if pooling_record.sample_id:
                    pooling_by_sample[pooling_record.sample_id] = pooling_record

        library_to_index_pools = defaultdict(list)
        sample_to_index_pools = defaultdict(list)
        if library_ids or sample_ids:
            index_pool_prefetches = []
            if library_ids:
                index_pool_prefetches.append(
                    Prefetch(
                        "libraries",
                        queryset=Library.objects.filter(id__in=library_ids).only(
                            "id", "barcode", "name"
                        ),
                    )
                )
            if sample_ids:
                index_pool_prefetches.append(
                    Prefetch(
                        "samples",
                        queryset=Sample.objects.filter(id__in=sample_ids).only(
                            "id", "barcode", "name"
                        ),
                    )
                )

            index_pools_qs = (
                IndexPool.objects.filter(
                    Q(libraries__id__in=library_ids) | Q(samples__id__in=sample_ids)
                )
                .select_related("size", "user")
                .distinct()
            )
            if index_pool_prefetches:
                index_pools_qs = index_pools_qs.prefetch_related(*index_pool_prefetches)

            index_pools = list(index_pools_qs)

            for pool in index_pools:
                pool_entity_id = register_index_pool(pool)
                for library in pool.libraries.all():
                    if library.id in library_id_set:
                        library_to_index_pools[library.id].append(
                            {"@id": pool_entity_id}
                        )
                for sample in pool.samples.all():
                    if sample.id in sample_id_set:
                        sample_to_index_pools[sample.id].append({"@id": pool_entity_id})

        flowcell_entities = {}
        flowcells_by_request = defaultdict(list)
        lane_queryset = (
            Lane.objects.select_related("pool", "pool__size")
            .prefetch_related("pool__libraries", "pool__samples")
            .only(
                "id",
                "name",
                "loading_concentration",
                "phix",
                "completed",
                "pool_id",
            )
        )
        flowcells_qs = (
            Flowcell.objects.filter(requests__id__in=target_request_ids)
            .select_related("sequencer")
            .prefetch_related(
                Prefetch(
                    "requests",
                    queryset=accessible_requests.filter(id__in=target_request_ids).only(
                        "id", "name"
                    ),
                ),
                Prefetch("lanes", queryset=lane_queryset),
            )
            .distinct()
        )

        for flowcell in flowcells_qs:
            associated_requests = [
                req.id for req in flowcell.requests.all() if req.id in requests_by_id
            ]
            if not associated_requests:
                continue

            flowcell_base_data = _extract_model_fields(flowcell, prefix="flowcell_")
            flowcell_comments = _build_comments(flowcell_base_data)

            sequencer_id = register_sequencer(flowcell.sequencer)

            current_flowcell_lane_refs = []
            for lane in flowcell.lanes.all():
                lane_entity_id = register_lane(lane)
                if lane_entity_id:
                    current_flowcell_lane_refs.append({"@id": lane_entity_id})

            _append_comment(
                flowcell_comments,
                "flowcell_associated_requests",
                [
                    requests_by_id[req_id].name
                    for req_id in associated_requests
                    if req_id in requests_by_id
                ],
            )

            flowcell_entity_id = f"#flowcell-assay-{flowcell.id}"
            flowcell_data_id = f"#flowcell-data-{flowcell.id}"
            flowcell_process_id = f"#flowcell-process-{flowcell.id}"
            data_file_entities[flowcell_data_id] = {
                "@id": flowcell_data_id,
                "@type": "Dataset",
                "name": f"Flowcell export metadata for {flowcell.flowcell_id}",
                "identifier": _parkour_identifier("flowcell-data", flowcell.id),
                "comments": _deduplicate_comments(flowcell_comments),
            }
            _apply_additional_types(
                data_file_entities[flowcell_data_id], ISA_DATA_URI
            )
            process_entities[flowcell_process_id] = {
                "@id": flowcell_process_id,
                "@type": "CreateAction",
                "name": f"Sequencing metadata capture for flowcell {flowcell.flowcell_id}",
                "identifier": _parkour_identifier("flowcell-process", flowcell.id),
                "inputs": current_flowcell_lane_refs,
                "outputs": [{"@id": flowcell_data_id}],
                "comments": _deduplicate_comments(flowcell_comments),
            }
            _apply_additional_types(
                process_entities[flowcell_process_id],
                ISA_PROCESS_URI,
            )
            if sequencer_id:
                process_entities[flowcell_process_id]["hasInstrument"] = {
                    "@id": sequencer_id
                }
            flowcell_entities[flowcell_entity_id] = {
                "@id": flowcell_entity_id,
                "@type": "Dataset",
                "name": f"Flowcell {flowcell.flowcell_id}",
                "identifier": _parkour_identifier("flowcell-assay", flowcell.id),
                "measurementType": _ontology_annotation("sequencing"),
                "technologyType": _ontology_annotation("sequencing"),
                "technologyPlatform": (
                    flowcell.sequencer.name if flowcell.sequencer else None
                ),
                "dataFiles": [{"@id": flowcell_data_id}],
                "processSequence": [{"@id": flowcell_process_id}],
            }
            _apply_additional_types(
                flowcell_entities[flowcell_entity_id], ISA_ASSAY_URI
            )
            if sequencer_id:
                flowcell_entities[flowcell_entity_id]["hasInstrument"] = {
                    "@id": sequencer_id
                }
            if current_flowcell_lane_refs:
                flowcell_entities[flowcell_entity_id][
                    "hasLane"
                ] = current_flowcell_lane_refs

            for req_id in associated_requests:
                flowcells_by_request[req_id].append(flowcell_entity_id)

        samples_for_request = list(sample_data)
        libraries_for_request = list(library_data)

        now = timezone.now()
        now_iso = now.isoformat()
        published_date = now.date().isoformat()
        graph = []

        context_extensions = {
            "@base": "./",
            "Investigation": ISA_INVESTIGATION_URI,
            "Study": ISA_STUDY_URI,
            "Assay": ISA_ASSAY_URI,
            "Process": ISA_PROCESS_URI,
            "Data": ISA_DATA_URI,
            "Material": ISA_MATERIAL_URI,
            "Sample": ISA_SAMPLE_URI,
            "Library": ISA_LIBRARY_URI,
            "File": "https://schema.org/File",
            "MediaObject": "https://schema.org/MediaObject",
            "Organism": ISA_ORGANISM_URI,
            "Protocol": ISA_PROTOCOL_URI,
            "Instrument": ISA_INSTRUMENT_URI,
            "Pool": ISA_POOL_URI,
            "Lane": ISA_LANE_URI,
            "SoftwareApplication": "https://schema.org/SoftwareApplication",
            "CreateAction": "https://schema.org/CreateAction",
            "Thing": "https://schema.org/Thing",
            "HowTo": "https://schema.org/HowTo",
            "PropertyValue": "https://schema.org/PropertyValue",
            "Person": "https://schema.org/Person",
            "Organization": "https://schema.org/Organization",
            "additionalType": {
                "@id": "https://schema.org/additionalType",
                "@type": "@id",
            },
            "hasPart": {"@id": "https://schema.org/hasPart", "@type": "@id"},
            "hasAssay": {"@id": "https://w3id.org/isa/hasAssay", "@type": "@id"},
            "hasInput": {"@id": "https://w3id.org/isa/hasInput", "@type": "@id"},
            "hasOutput": {"@id": "https://w3id.org/isa/hasOutput", "@type": "@id"},
            "studies": {"@id": "https://w3id.org/isa/studies", "@type": "@id"},
            "people": {"@id": "https://w3id.org/isa/people", "@type": "@id"},
            "materials": {"@id": "https://w3id.org/isa/materials"},
            "sources": {"@id": "https://w3id.org/isa/sources", "@type": "@id"},
            "samples": {"@id": "https://w3id.org/isa/samples", "@type": "@id"},
            "otherMaterials": {
                "@id": "https://w3id.org/isa/otherMaterials",
                "@type": "@id",
            },
            "processSequence": {
                "@id": "https://w3id.org/isa/processSequence",
                "@type": "@id",
            },
            "assays": {"@id": "https://w3id.org/isa/assays", "@type": "@id"},
            "dataFiles": {"@id": "https://w3id.org/isa/dataFiles", "@type": "@id"},
            "executesProtocol": {
                "@id": "https://w3id.org/isa/executesProtocol",
                "@type": "@id",
            },
            "inputs": {"@id": "https://w3id.org/isa/inputs", "@type": "@id"},
            "outputs": {"@id": "https://w3id.org/isa/outputs", "@type": "@id"},
            "comments": {"@id": "https://w3id.org/isa/comments"},
            "measurementType": {"@id": "https://w3id.org/isa/measurementType"},
            "technologyType": {"@id": "https://w3id.org/isa/technologyType"},
            "technologyPlatform": {"@id": "https://w3id.org/isa/technologyPlatform"},
            "protocols": {"@id": "https://w3id.org/isa/protocols", "@type": "@id"},
            "executesLabProtocol": {
                "@id": "https://bioschemas.org/executesLabProtocol",
                "@type": "@id",
            },
            "parameterValue": {"@id": "https://bioschemas.org/parameterValue"},
            "organism": {"@id": "https://schema.org/taxonomicRange", "@type": "@id"},
            "libraryType": {"@id": "https://schema.org/additionalType", "@type": "@id"},
            "readLength": {
                "@id": "https://schema.org/measurementTechnique",
                "@type": "@id",
            },
            "indexType": {"@id": "https://schema.org/category", "@type": "@id"},
            "nucleicAcidType": {"@id": "https://schema.org/material", "@type": "@id"},
            "derivedFrom": {"@id": "https://w3id.org/isa/derivesFrom", "@type": "@id"},
            "creator": {"@id": "https://schema.org/creator", "@type": "@id"},
            "mentions": {"@id": "https://schema.org/mentions", "@type": "@id"},
            "requestContext": {
                "@id": "https://schema.org/isPartOf",
                "@type": "@id",
            },
            "member": {"@id": "https://schema.org/member", "@type": "@id"},
            "affiliatedOrganization": {
                "@id": "https://schema.org/affiliation",
                "@type": "@id",
            },
            "principalInvestigator": {
                "@id": "https://w3id.org/isa/principalInvestigator",
                "@type": "@id",
            },
            "usesProtocol": {
                "@id": "https://w3id.org/isa/usesProtocol",
                "@type": "@id",
            },
            "associatedPool": {"@id": "https://schema.org/isRelatedTo", "@type": "@id"},
            "hasInstrument": {
                "@id": "https://w3id.org/isa/hasInstrument",
                "@type": "@id",
            },
            "hasLane": {"@id": "https://w3id.org/isa/hasPart", "@type": "@id"},
            "costUnit": {"@id": "https://schema.org/identifier", "@type": "@id"},
            "instrument": {"@id": "https://schema.org/instrument", "@type": "@id"},
            "result": {"@id": "https://schema.org/result", "@type": "@id"},
            "object": {"@id": "https://schema.org/object", "@type": "@id"},
            "agent": {"@id": "https://schema.org/agent", "@type": "@id"},
            "isPartOf": {"@id": "https://schema.org/isPartOf", "@type": "@id"},
            "about": {"@id": "https://schema.org/about", "@type": "@id"},
        }

        graph.append(_metadata_descriptor_entity())
        graph.append(_software_entity())

        dataset_additional_properties = []
        _append_property(dataset_additional_properties, "generated_at", now_iso)
        if barcode_values:
            _append_property(
                dataset_additional_properties,
                "requested_barcodes",
                ", ".join(barcode_values),
            )
        if request_values:
            _append_property(
                dataset_additional_properties,
                "requested_requests",
                ", ".join(request_values),
            )
        if missing_barcodes:
            _append_property(
                dataset_additional_properties,
                "missing_barcodes",
                ", ".join(missing_barcodes),
            )
        if missing_requests:
            _append_property(
                dataset_additional_properties,
                "missing_requests",
                ", ".join(missing_requests),
            )
        if non_completed_records:
            _append_property(
                dataset_additional_properties,
                "skipped_non_delivered_records",
                ", ".join(non_completed_records),
            )
        if selected_sections:
            _append_property(
                dataset_additional_properties,
                "requested_sections",
                sorted(selected_sections),
            )
        if is_multi_request_export:
            _append_property(
                dataset_additional_properties,
                "requested_request_ids",
                ", ".join(str(request_id) for request_id in target_request_ids),
            )

        request_display_name = (
            f"Parkour RO-Crate export ({len(target_request_ids)} requests)"
            if is_multi_request_export
            else root_request.name or f"Request {single_request_id}"
        )
        request_timestamp = _normalise_property_value(
            getattr(root_request, "create_time", None)
        )
        request_data = _extract_request_metadata(root_request)

        dataset_entity = {
            "@id": "./",
            "@type": "Dataset",
            "name": request_display_name,
            "identifier": (
                _parkour_identifier(
                    "ro-crate-export", "-".join(str(pk) for pk in target_request_ids)
                )
                if is_multi_request_export
                else _parkour_identifier("request", single_request_id)
            ),
            "description": (
                f"Parkour metadata export for {len(target_request_ids)} selected requests."
                if is_multi_request_export
                else root_request.description or ""
            ),
            "dateCreated": request_timestamp or now_iso,
            "datePublished": published_date,
            "conformsTo": [{"@id": NFDI4PLANTS_ISA_PROFILE_URI}],
            "license": {"@id": RO_CRATE_LICENSE_ID},
            "creator": {"@id": PARKOUR_SOFTWARE_ID},
            "studies": [{"@id": f"#study-{single_request_id}"}],
            "people": [],
            "mentions": [],
            "hasPart": [],
            "comments": _deduplicate_comments(_build_comments(request_data)),
            "additionalProperty": _deduplicate_properties(
                dataset_additional_properties
            ),
        }
        _apply_additional_types(dataset_entity, ISA_INVESTIGATION_URI)

        for current_request in sorted(
            requests_by_id.values(), key=lambda request_obj: request_obj.id
        ):
            request_context_id = f"#request-context-{current_request.id}"
            request_context_entities[request_context_id] = (
                _build_request_context_entity(current_request)
            )
            dataset_entity["mentions"].append({"@id": request_context_id})
            dataset_entity["hasPart"].append({"@id": request_context_id})

        request_id = single_request_id
        request_obj = root_request

        study_id = f"#study-{request_id}"
        dataset_entity["mentions"].append({"@id": study_id})
        dataset_entity["hasPart"].append({"@id": study_id})

        investigation_people = []
        cost_unit_id = register_cost_unit(request_obj.cost_unit)
        if cost_unit_id:
            dataset_entity["mentions"].append({"@id": cost_unit_id})

        user_org_id = None
        if request_obj.user and request_obj.user.organization:
            user_org_id = register_organization(request_obj.user.organization)
            if user_org_id:
                dataset_entity["mentions"].append({"@id": user_org_id})

        user_pi_id = None
        if request_obj.user:
            user_pi_id = register_principal_investigator(
                getattr(request_obj.user, "pi", None)
            )
            if user_pi_id:
                dataset_entity["mentions"].append({"@id": user_pi_id})
                investigation_people.append({"@id": user_pi_id})

        user_obj = getattr(request_obj, "user", None)
        if user_obj:
            exporting_user_id = register_user_entity(user_obj)
            investigation_people.insert(0, {"@id": exporting_user_id})
            dataset_entity["mentions"].append({"@id": exporting_user_id})
        dataset_entity["people"] = _deduplicate_ref_list(investigation_people)
        if cost_unit_id:
            dataset_entity["costUnit"] = {"@id": cost_unit_id}
        if user_org_id:
            dataset_entity["affiliatedOrganization"] = {"@id": user_org_id}
        if user_pi_id:
            dataset_entity["principalInvestigator"] = {"@id": user_pi_id}

        study_properties = {
            "study_request_identifier": request_display_name,
            "study_samples_count": len(samples_for_request),
            "study_libraries_count": len(libraries_for_request),
        }

        study_protocol_refs = []
        study_source_refs = []
        study_sample_refs = []
        study_other_material_refs = []
        study_process_refs = []
        study_assay_refs = []
        study_people = _deduplicate_ref_list(investigation_people)

        study_entity = {
            "@id": study_id,
            "@type": "Dataset",
            "identifier": _parkour_identifier("study", request_id),
            "name": f"Study for {request_display_name}",
            "description": request_obj.description or "",
            "dateCreated": request_timestamp,
            "datePublished": published_date,
            "people": study_people,
            "protocols": [],
            "materials": {
                "sources": [],
                "samples": [],
                "otherMaterials": [],
            },
            "processSequence": [],
            "assays": [],
            "comments": _build_comments(study_properties),
        }
        _apply_additional_types(study_entity, ISA_STUDY_URI)

        request_file_refs = []
        for current_request in requests_by_id.values():
            for request_file in current_request.files.all():
                request_file_id = register_request_file(request_file, current_request)
                if not request_file_id:
                    continue
                request_file_refs.append({"@id": request_file_id})
                dataset_entity["mentions"].append({"@id": request_file_id})
        if request_file_refs:
            deduped_request_file_refs = _deduplicate_ref_list(request_file_refs)
            study_entity["hasPart"] = deduped_request_file_refs
            dataset_entity["hasPart"].extend(deduped_request_file_refs)

        for sample_entry in samples_for_request:
                source_id = f"#source-sample-{sample_entry.sample_id}"
                sample_material_id = f"#sample-material-{sample_entry.sample_id}"
                sample_process_id = f"#sample-process-{sample_entry.sample_id}"
                sample_assay_id = f"#sample-assay-{sample_entry.sample_id}"
                sample_data_id = f"#sample-data-{sample_entry.sample_id}"

                study_source_refs.append({"@id": source_id})
                study_sample_refs.append({"@id": sample_material_id})
                study_process_refs.append({"@id": sample_process_id})
                study_assay_refs.append({"@id": sample_assay_id})
                dataset_entity["mentions"].extend(
                    [
                        {"@id": source_id},
                        {"@id": sample_material_id},
                        {"@id": sample_process_id},
                        {"@id": sample_assay_id},
                        {"@id": sample_data_id},
                    ]
                )

                sample_model = samples_by_id.get(sample_entry.sample_id)
                sample_data = {}
                if sample_model:
                    sample_data.update(
                        _extract_model_fields(sample_model, prefix="sample_db_")
                    )
                sample_data.update(
                    _extract_model_fields(sample_entry, prefix="sample_mv_")
                )
                sample_comments = _build_comments(sample_data)

                if sample_model:
                    organism_id = register_organism(sample_model.organism)
                    if organism_id:
                        dataset_entity["mentions"].append({"@id": organism_id})
                    protocol_id = register_protocol(sample_model.library_protocol)
                    if protocol_id:
                        study_protocol_refs.append({"@id": protocol_id})
                        dataset_entity["mentions"].append({"@id": protocol_id})
                    library_type_id = register_library_type(sample_model.library_type)
                    if library_type_id:
                        dataset_entity["mentions"].append({"@id": library_type_id})
                    read_length_id = register_read_length(sample_model.read_length)
                    if read_length_id:
                        dataset_entity["mentions"].append({"@id": read_length_id})
                    index_type_id = register_index_type(sample_model.index_type)
                    if index_type_id:
                        dataset_entity["mentions"].append({"@id": index_type_id})
                    nucleic_acid_id = register_nucleic_acid(
                        sample_model.nucleic_acid_type
                    )
                    if nucleic_acid_id:
                        dataset_entity["mentions"].append({"@id": nucleic_acid_id})

                library_prep = library_preparations_by_sample.get(
                    sample_entry.sample_id
                )
                if library_prep:
                    sample_comments.extend(
                        _build_comments(
                            _extract_model_fields(
                                library_prep, prefix="library_preparation_"
                            )
                        )
                    )

                sample_pooling = pooling_by_sample.get(sample_entry.sample_id)
                if sample_pooling:
                    sample_comments.extend(
                        _build_comments(
                            _extract_model_fields(sample_pooling, prefix="pooling_")
                        )
                    )

                sample_pool_refs = sample_to_index_pools.get(sample_entry.sample_id, [])
                if sample_pool_refs:
                    dataset_entity["mentions"].extend(sample_pool_refs)
                sample_comments = _deduplicate_comments(sample_comments)

                source_entities[source_id] = {
                    "@id": source_id,
                    "@type": "Thing",
                    "name": f"Source for {sample_entry.name}",
                    "identifier": _parkour_identifier(
                        "source-sample", sample_entry.sample_id
                    ),
                    "comments": _deduplicate_comments(
                        [
                            {
                                "name": "source_request_identifier",
                                "value": sample_entry.request_name or request_display_name,
                            }
                        ]
                    ),
                }
                _apply_additional_types(
                    source_entities[source_id], ISA_MATERIAL_URI
                )
                sample_entity = {
                    "@id": sample_material_id,
                    "@type": "Thing",
                    "name": sample_entry.name,
                    "identifier": sample_entry.barcode,
                    "comments": sample_comments,
                    "derivedFrom": [{"@id": source_id}],
                }
                _apply_additional_types(
                    sample_entity,
                    ISA_MATERIAL_URI,
                    ISA_SAMPLE_URI,
                )
                if sample_model and sample_model.library_type:
                    sample_entity["libraryType"] = {
                        "@id": f"#library-type-{sample_model.library_type.id}"
                    }
                if sample_model and sample_model.read_length:
                    sample_entity["readLength"] = {
                        "@id": f"#read-length-{sample_model.read_length.id}"
                    }
                if sample_model and sample_model.index_type:
                    sample_entity["indexType"] = {
                        "@id": f"#index-type-{sample_model.index_type.id}"
                    }
                if sample_model and sample_model.organism:
                    sample_entity["organism"] = {
                        "@id": f"#organism-{sample_model.organism.id}"
                    }
                if sample_model and sample_model.nucleic_acid_type:
                    sample_entity["nucleicAcidType"] = {
                        "@id": f"#nucleic-acid-type-{sample_model.nucleic_acid_type.id}"
                    }
                if sample_pool_refs:
                    sample_entity["associatedPool"] = _deduplicate_ref_list(
                        sample_pool_refs
                    )
                process_entities[sample_process_id] = {
                    "@id": sample_process_id,
                    "@type": "CreateAction",
                    "name": f"Sample metadata capture for {sample_entry.name}",
                    "identifier": _parkour_identifier(
                        "sample-process", sample_entry.sample_id
                    ),
                    "inputs": [{"@id": source_id}],
                    "outputs": [{"@id": sample_material_id}, {"@id": sample_data_id}],
                }
                _apply_additional_types(
                    process_entities[sample_process_id], ISA_PROCESS_URI
                )
                if sample_model and sample_model.library_protocol:
                    process_entities[sample_process_id]["executesProtocol"] = {
                        "@id": f"#protocol-{sample_model.library_protocol.id}"
                    }
                data_file_entities[sample_data_id] = {
                    "@id": sample_data_id,
                    "@type": "Dataset",
                    "name": f"Sample export metadata for {sample_entry.name}",
                    "identifier": _parkour_identifier(
                        "sample-data", sample_entry.sample_id
                    ),
                    "comments": _build_comments(
                        {
                            "sample_export_identifier": sample_entry.barcode,
                            "sample_export_request": sample_entry.request_name
                            or request_display_name,
                        }
                    ),
                }
                _apply_additional_types(
                    data_file_entities[sample_data_id], ISA_DATA_URI
                )
                sample_assay_entity = {
                    "@id": sample_assay_id,
                    "@type": "Dataset",
                    "identifier": _parkour_identifier(
                        "sample-assay", sample_entry.sample_id
                    ),
                    "measurementType": _ontology_annotation("sample metadata export"),
                    "technologyType": _ontology_annotation("metadata capture"),
                    "materials": {"samples": [{"@id": sample_material_id}]},
                    "dataFiles": [{"@id": sample_data_id}],
                    "processSequence": [{"@id": sample_process_id}],
                }
                _apply_additional_types(
                    sample_assay_entity, ISA_ASSAY_URI
                )
                graph.append(sample_entity)
                graph.append(sample_assay_entity)

        for library_entry in libraries_for_request:
                library_material_id = f"#library-material-{library_entry.library_id}"
                library_process_id = f"#library-process-{library_entry.library_id}"
                assay_id = f"#library-assay-{library_entry.library_id}"
                library_data_id = f"#library-data-{library_entry.library_id}"

                study_other_material_refs.append({"@id": library_material_id})
                study_process_refs.append({"@id": library_process_id})
                study_assay_refs.append({"@id": assay_id})
                dataset_entity["mentions"].extend(
                    [
                        {"@id": library_material_id},
                        {"@id": library_process_id},
                        {"@id": assay_id},
                        {"@id": library_data_id},
                    ]
                )

                library_model = libraries_by_id.get(library_entry.library_id)
                library_material_data = {}
                if library_model:
                    library_material_data.update(
                        _extract_model_fields(library_model, prefix="library_db_")
                    )

                library_comments = _build_comments(library_material_data)

                if library_model:
                    organism_id = register_organism(library_model.organism)
                    if organism_id:
                        dataset_entity["mentions"].append({"@id": organism_id})
                    protocol_id = register_protocol(library_model.library_protocol)
                    if protocol_id:
                        study_protocol_refs.append({"@id": protocol_id})
                        dataset_entity["mentions"].append({"@id": protocol_id})
                    library_type_id = register_library_type(library_model.library_type)
                    if library_type_id:
                        dataset_entity["mentions"].append({"@id": library_type_id})
                    read_length_id = register_read_length(library_model.read_length)
                    if read_length_id:
                        dataset_entity["mentions"].append({"@id": read_length_id})
                    index_type_id = register_index_type(library_model.index_type)
                    if index_type_id:
                        dataset_entity["mentions"].append({"@id": index_type_id})

                library_pooling = pooling_by_library.get(library_entry.library_id)
                if library_pooling:
                    library_comments.extend(
                        _build_comments(
                            _extract_model_fields(library_pooling, prefix="pooling_")
                        )
                    )

                library_pool_refs = library_to_index_pools.get(
                    library_entry.library_id, []
                )
                if library_pool_refs:
                    dataset_entity["mentions"].extend(library_pool_refs)
                library_comments = _deduplicate_comments(library_comments)

                library_entity = {
                    "@id": library_material_id,
                    "@type": "Thing",
                    "name": library_entry.name,
                    "identifier": library_entry.barcode,
                    "comments": library_comments,
                }
                _apply_additional_types(
                    library_entity,
                    ISA_MATERIAL_URI,
                    ISA_LIBRARY_URI,
                )
                if library_model and library_model.organism:
                    library_entity["organism"] = {
                        "@id": f"#organism-{library_model.organism.id}"
                    }
                if library_model and library_model.library_type:
                    library_entity["libraryType"] = {
                        "@id": f"#library-type-{library_model.library_type.id}"
                    }
                if library_model and library_model.read_length:
                    library_entity["readLength"] = {
                        "@id": f"#read-length-{library_model.read_length.id}"
                    }
                if library_model and library_model.index_type:
                    library_entity["indexType"] = {
                        "@id": f"#index-type-{library_model.index_type.id}"
                    }
                if library_pool_refs:
                    library_entity["associatedPool"] = _deduplicate_ref_list(
                        library_pool_refs
                    )

                assay_comments = _deduplicate_comments(
                    _build_comments(
                        _extract_model_fields(library_entry, prefix="library_mv_")
                    )
                )
                process_entities[library_process_id] = {
                    "@id": library_process_id,
                    "@type": "CreateAction",
                    "name": f"Library metadata capture for {library_entry.name}",
                    "identifier": _parkour_identifier(
                        "library-process", library_entry.library_id
                    ),
                    "inputs": [{"@id": library_material_id}],
                    "outputs": [{"@id": library_data_id}],
                    "comments": assay_comments,
                }
                _apply_additional_types(
                    process_entities[library_process_id], ISA_PROCESS_URI
                )
                if library_model and library_model.library_protocol:
                    process_entities[library_process_id]["executesProtocol"] = {
                        "@id": f"#protocol-{library_model.library_protocol.id}"
                    }
                data_file_entities[library_data_id] = {
                    "@id": library_data_id,
                    "@type": "Dataset",
                    "name": f"Library export metadata for {library_entry.name}",
                    "identifier": _parkour_identifier(
                        "library-data", library_entry.library_id
                    ),
                    "comments": _build_comments(
                        {
                            "library_export_identifier": library_entry.barcode,
                            "library_export_request": library_entry.request_name
                            or request_display_name,
                        }
                    ),
                }
                _apply_additional_types(
                    data_file_entities[library_data_id], ISA_DATA_URI
                )
                assay_entity = {
                    "@id": assay_id,
                    "@type": "Dataset",
                    "identifier": _parkour_identifier(
                        "library-assay", library_entry.library_id
                    ),
                    "name": f"Assay for library {library_entry.name}",
                    "measurementType": _ontology_annotation("library metadata export"),
                    "technologyType": _ontology_annotation("metadata capture"),
                    "materials": {"otherMaterials": [{"@id": library_material_id}]},
                    "dataFiles": [{"@id": library_data_id}],
                    "processSequence": [{"@id": library_process_id}],
                }
                _apply_additional_types(assay_entity, ISA_ASSAY_URI)

                graph.append(library_entity)
                graph.append(assay_entity)

        flowcell_ids_for_request = []
        for request_id in target_request_ids:
            flowcell_ids_for_request.extend(flowcells_by_request.get(request_id, []))
        if flowcell_ids_for_request:
            seen_flowcells = set()
            for flowcell_entity_id in flowcell_ids_for_request:
                if flowcell_entity_id in seen_flowcells:
                    continue
                seen_flowcells.add(flowcell_entity_id)
                study_assay_refs.append({"@id": flowcell_entity_id})
                dataset_entity["mentions"].append({"@id": flowcell_entity_id})
                flowcell_suffix = flowcell_entity_id.replace("#flowcell-assay-", "")
                dataset_entity["mentions"].append(
                    {"@id": f"#flowcell-data-{flowcell_suffix}"}
                )
                dataset_entity["mentions"].append(
                    {"@id": f"#flowcell-process-{flowcell_suffix}"}
                )
            _append_comment(
                study_entity["comments"],
                "flowcell_assays",
                sorted(seen_flowcells),
            )

        study_entities_to_append = [study_entity]
        if is_multi_request_export:
            dataset_entity["studies"] = []
            study_entities_to_append = []
            for current_request_id in target_request_ids:
                current_request = requests_by_id.get(current_request_id)
                if current_request is None:
                    continue

                current_samples = [
                    entry
                    for entry in samples_for_request
                    if entry.request_id == current_request_id
                ]
                current_libraries = [
                    entry
                    for entry in libraries_for_request
                    if entry.request_id == current_request_id
                ]
                current_study_id = f"#study-{current_request_id}"
                current_source_refs = [
                    {"@id": f"#source-sample-{entry.sample_id}"}
                    for entry in current_samples
                ]
                current_sample_refs = [
                    {"@id": f"#sample-material-{entry.sample_id}"}
                    for entry in current_samples
                ]
                current_library_refs = [
                    {"@id": f"#library-material-{entry.library_id}"}
                    for entry in current_libraries
                ]
                current_process_refs = [
                    {"@id": f"#sample-process-{entry.sample_id}"}
                    for entry in current_samples
                ] + [
                    {"@id": f"#library-process-{entry.library_id}"}
                    for entry in current_libraries
                ]
                current_assay_refs = [
                    {"@id": f"#sample-assay-{entry.sample_id}"}
                    for entry in current_samples
                ] + [
                    {"@id": f"#library-assay-{entry.library_id}"}
                    for entry in current_libraries
                ]

                for flowcell_entity_id in flowcells_by_request.get(
                    current_request_id, []
                ):
                    current_assay_refs.append({"@id": flowcell_entity_id})

                dataset_entity["studies"].append({"@id": current_study_id})
                dataset_entity["mentions"].append({"@id": current_study_id})
                dataset_entity["hasPart"].append({"@id": current_study_id})

                current_study_entity = {
                    "@id": current_study_id,
                    "@type": "Dataset",
                    "identifier": _parkour_identifier(
                        "study", current_request_id
                    ),
                    "name": f"Study for {current_request.name or f'Request {current_request_id}'}",
                    "description": current_request.description or "",
                    "dateCreated": _normalise_property_value(
                        getattr(current_request, "create_time", None)
                    ),
                    "datePublished": published_date,
                    "materials": {
                        "sources": _deduplicate_ref_list(current_source_refs),
                        "samples": _deduplicate_ref_list(current_sample_refs),
                        "otherMaterials": _deduplicate_ref_list(
                            current_library_refs
                        ),
                    },
                    "processSequence": _deduplicate_ref_list(
                        current_process_refs
                    ),
                    "assays": _deduplicate_ref_list(current_assay_refs),
                    "comments": _build_comments(
                        {
                            "study_request_identifier": current_request.name,
                            "study_samples_count": len(current_samples),
                            "study_libraries_count": len(current_libraries),
                        }
                    ),
                }
                _apply_additional_types(
                    current_study_entity, ISA_STUDY_URI
                )
                study_entities_to_append.append(current_study_entity)
        else:
            study_entity["protocols"] = _deduplicate_ref_list(study_protocol_refs)
            study_entity["materials"]["sources"] = _deduplicate_ref_list(
                study_source_refs
            )
            study_entity["materials"]["samples"] = _deduplicate_ref_list(
                study_sample_refs
            )
            study_entity["materials"]["otherMaterials"] = _deduplicate_ref_list(
                study_other_material_refs
            )
            study_entity["processSequence"] = _deduplicate_ref_list(
                study_process_refs
            )
            study_entity["assays"] = _deduplicate_ref_list(study_assay_refs)
            study_entity["comments"] = _deduplicate_comments(
                study_entity["comments"]
            )

        graph.extend(study_entities_to_append)

        exporter_entity_id = None
        exporting_user = getattr(request, "user", None)
        if getattr(exporting_user, "is_authenticated", False):
            exporter_entity_id = register_user_entity(exporting_user)
            if exporter_entity_id:
                dataset_entity["mentions"].append({"@id": exporter_entity_id})

        export_action_entity = _export_action_entity(
            now_iso,
            object_refs=dataset_entity.get("mentions", []),
            agent_ref=exporter_entity_id,
        )
        dataset_entity["mentions"].append({"@id": RO_CRATE_EXPORT_ACTION_ID})

        graph.extend(organization_entities.values())
        graph.extend(organism_entities.values())
        graph.extend(pi_entities.values())
        graph.extend(cost_unit_entities.values())
        graph.extend(protocol_entities.values())
        graph.extend(library_type_entities.values())
        graph.extend(read_length_entities.values())
        graph.extend(index_type_entities.values())
        graph.extend(nucleic_acid_entities.values())
        graph.extend(index_pool_entities.values())
        graph.extend(flowcell_entities.values())
        graph.extend(sequencer_entities.values())
        graph.extend(lane_entities.values())
        graph.extend(request_file_entities.values())
        graph.extend(request_context_entities.values())
        graph.extend(source_entities.values())
        graph.extend(process_entities.values())
        graph.extend(data_file_entities.values())
        graph.extend(user_entities.values())

        dataset_entity["mentions"] = _deduplicate_ref_list(dataset_entity["mentions"])
        dataset_entity["hasPart"] = _deduplicate_ref_list(dataset_entity["hasPart"])

        graph.insert(
            1,
            dataset_entity,
        )

        graph.insert(2, _license_entity())
        graph.insert(3, export_action_entity)

        ro_crate = {
            "@context": [
                RO_CRATE_CONTEXT_URI,
                context_extensions,
            ],
            "@graph": graph,
        }
        ro_crate = _align_to_nfdi4plants_profile(ro_crate)
        ro_crate = _filter_ro_crate_sections(ro_crate, selected_sections)
        archive_stub = _archive_stub_for_requests(requests_by_id, target_request_ids)
        archive_name = f"{archive_stub}_ro_crate.zip"
        file_entries = [
            (archive_path, source_path)
            for archive_path, source_path in request_file_archives.items()
            if archive_path
            and source_path
            and any(
                entry.get("@id") == archive_path for entry in ro_crate.get("@graph", [])
            )
        ]
        return _build_ro_crate_response(
            request,
            ro_crate,
            archive_name,
            file_entries,
            non_completed_records,
        )
__all__ = ["GenerateROCrate"]
