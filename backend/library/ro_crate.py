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


def _normalise_preview(raw_preview):
    if raw_preview is None:
        return False
    if raw_preview == "true":
        return True
    return Response(
        {"error": "The 'preview' query parameter must be 'true' when provided."},
        status=400,
    )


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


def _archive_stub(requests_by_id, request_ids):
    ids = [
        str(request_id)
        for request_id in request_ids
        if request_id in requests_by_id
    ]
    if not ids:
        return "parkour"
    stub = "_".join(ids)
    return stub[:RO_CRATE_ARCHIVE_STUB_MAX_LENGTH].rstrip("._-") or "parkour"


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
    existing = {
        item.get("@id") if isinstance(item, dict) else item
        for item in values
    }
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
    request_folder = _safe_archive_component(
        f"request-{request_obj.id}_{request_obj.name or f'request_{request_obj.id}'}",
        f"request-{request_obj.id}",
    )
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
    if not barcodes and not requests:
        return Response(
            {
                "error": "Provide at least one comma separated barcode value or request name via the 'barcodes' or 'requests' query parameters."
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
        request_name for request_name in requests if request_name not in found_request_names
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
            skipped.append(getattr(row, "barcode", None) or getattr(row, "name", None) or str(row))
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
        archive_name = f"{_archive_stub(requests_by_id, self.selection.target_request_ids)}_ro_crate.zip"
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
        return CrateBuildResult(ro_crate, "parkour_ro_crate.zip", [])

    def _library_models(self):
        ids = [row.library_id for row in self.selection.library_rows]
        return {
            library.id: library
            for library in Library.objects.filter(id__in=ids).select_related(
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            ).prefetch_related(
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
            for sample in Sample.objects.filter(id__in=ids).select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "organism",
                "read_length",
                "index_type",
            ).prefetch_related(
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
                {key: value for key, value in entity.items() if value not in (None, "", [], {})}
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
                    "comments": _comments_from_mapping(
                        request_metadata, "request"
                    ),
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
                            "request_file_storage_path": getattr(file_field, "name", None),
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
            self._add_data(data_id, f"Sample export metadata for {row.name}", "sample-data", row.sample_id, "samples")
            self._add_assay(assay_id, f"Assay for sample {row.name}", sample_id, process_id, data_id, "samples")
            record_entity_ids = [source_id, sample_id, process_id, data_id, assay_id]
            self._link_to_record_requests(sample, model, row.request_id, record_entity_ids)

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
            self._add_data(data_id, f"Library export metadata for {row.name}", "library-data", row.library_id, "libraries")
            self._add_assay(assay_id, f"Assay for library {row.name}", library_id, process_id, data_id, "libraries")
            self._link_to_record_requests(
                library, model, row.request_id, [library_id, process_id, data_id, assay_id]
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
            ("nucleicAcidType", "nucleic_acid_type", "nucleic_acid_types", ISA_MATERIAL_URI),
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
                    "identifier": _parkour_identifier(attr_name.replace("_", "-"), value.id),
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
            entity["selectedIndexPair"] = _ref(self._add_index_pair(index_pair, section))

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
        self._add(entity, "index_types" if section in {"libraries", "samples"} else section)
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
                        for library_id in lane.pool.libraries.values_list("id", flat=True)
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
                        "associatedPool": _ref(lane_pool_id)
                        if lane_pool_id
                        else None,
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
                            _extract_model_fields(
                                flowcell.sequencer, "sequencer_"
                            ),
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
            request_id for request_id in request_ids if request_id in self.requests_by_id
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
            "readLength": {"@id": "http://schema.org/measurementTechnique", "@type": "@id"},
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
    if entity_id.startswith("#request-context-") or entity_id.startswith("#request-file-"):
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
                (key, _filter_refs(nested, kept_ids))
                for key, nested in value.items()
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


def _crate_response(preview_requested, result, skipped_records):
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
            selection.preview_requested, result, selection.skipped_records
        )


__all__ = ["GenerateROCrate"]
