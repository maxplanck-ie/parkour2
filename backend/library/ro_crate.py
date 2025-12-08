import json
import uuid
from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal
from itertools import chain

from django.apps import apps
from django.db.models import Q, Prefetch
from django.db.models.fields.files import FieldFile
from django.http import JsonResponse
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


def _extract_model_fields(instance, prefix=""):
    if instance is None:
        return {}
    data = {}
    for field in instance._meta.concrete_fields:
        field_name = field.name
        if field_name.startswith("removed_") or field_name == "archived":
            continue
        try:
            value = field.value_from_object(instance)
        except Exception:  # pragma: no cover - defensive
            continue
        data[f"{prefix}{field_name}"] = value
    return data


def _build_property_values(data):
    properties = []
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        normalised = _normalise_property_value(value)
        if normalised in (None, "", [], {}):
            continue
        properties.append(
            {
                "@type": "PropertyValue",
                "name": key,
                "value": normalised,
            }
        )
    return properties


def _extend_properties_from_instance(properties, instance, prefix):
    if instance is None:
        return
    properties.extend(
        _build_property_values(_extract_model_fields(instance, prefix=prefix))
    )


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


class GenerateROCrate(viewsets.ViewSet):
    def list(self, request):
        barcode_values = _parse_csv_values(request.query_params.get("barcodes"))
        request_values = _parse_csv_values(request.query_params.get("requests"))

        if not barcode_values and not request_values:
            return Response(
                {
                    "error": "Provide at least one comma separated barcode value or request name via the 'barcodes' or 'requests' query parameters."
                },
                status=400,
            )

        accessible_requests = get_accessible_requests(request)
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

        target_request_ids = request_ids_from_data.union(request_ids_from_names)
        if not target_request_ids:
            timestamp = timezone.now().isoformat()
            return Response(
                {
                    "@context": [
                        "https://w3id.org/ro/crate/1.1/context",
                        {"@base": "./"},
                    ],
                    "@graph": [
                        {
                            "@id": "ro-crate-metadata.json",
                            "@type": "CreativeWork",
                            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                            "about": {"@id": "./"},
                        },
                        {
                            "@id": "./",
                            "@type": "Dataset",
                            "name": "RO-Crate export",
                            "dateCreated": timestamp,
                            "description": "No matching barcodes or requests were found.",
                        },
                    ],
                }
            )

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
        requests_by_id = {req.id: req for req in requests_qs}

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

        def register_organization(organization):
            if organization is None:
                return None
            entity_id = f"#organization-{organization.id}"
            if entity_id not in organization_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(organization, prefix="organization_")
                    )
                )
                organization_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Organization",
                    "name": organization.name or str(organization),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_principal_investigator(pi_obj):
            if pi_obj is None:
                return None
            entity_id = f"#principal-investigator-{pi_obj.id}"
            if entity_id not in pi_entities:
                properties = _build_property_values(
                    _extract_model_fields(pi_obj, prefix="principal_investigator_")
                )
                org_id = register_organization(pi_obj.organization)
                if org_id:
                    _append_property(
                        properties, "affiliatedOrganization", {"@id": org_id}
                    )
                pi_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Person",
                    "name": pi_obj.name or str(pi_obj),
                    "additionalProperty": _deduplicate_properties(properties),
                }
            return entity_id

        def register_organism(organism):
            if organism is None:
                return None
            entity_id = f"#organism-{organism.id}"
            if entity_id not in organism_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(organism, prefix="organism_")
                    )
                )
                organism_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Organism",
                    "name": organism.name or str(organism),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_cost_unit(cost_unit):
            if cost_unit is None:
                return None
            entity_id = f"#cost-unit-{cost_unit.id}"
            if entity_id not in cost_unit_entities:
                properties = _build_property_values(
                    _extract_model_fields(cost_unit, prefix="cost_unit_")
                )
                pi_id = register_principal_investigator(cost_unit.pi)
                if pi_id:
                    _append_property(
                        properties, "principalInvestigator", {"@id": pi_id}
                    )
                cost_unit_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": cost_unit.name or str(cost_unit),
                    "additionalProperty": _deduplicate_properties(properties),
                }
            return entity_id

        def register_protocol(protocol):
            if protocol is None:
                return None
            entity_id = f"#protocol-{protocol.id}"
            if entity_id not in protocol_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(protocol, prefix="protocol_")
                    )
                )
                protocol_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Protocol",
                    "name": protocol.name or str(protocol),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_library_type(library_type):
            if library_type is None:
                return None
            entity_id = f"#library-type-{library_type.id}"
            if entity_id not in library_type_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(library_type, prefix="library_type_")
                    )
                )
                library_type_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Material",
                    "name": library_type.name or str(library_type),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_read_length(read_length):
            if read_length is None:
                return None
            entity_id = f"#read-length-{read_length.id}"
            if entity_id not in read_length_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(read_length, prefix="read_length_")
                    )
                )
                read_length_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": read_length.name or str(read_length),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_index_type(index_type):
            if index_type is None:
                return None
            entity_id = f"#index-type-{index_type.id}"
            if entity_id not in index_type_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(index_type, prefix="index_type_")
                    )
                )
                index_type_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Thing",
                    "name": index_type.name or str(index_type),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_nucleic_acid(nucleic_acid):
            if nucleic_acid is None:
                return None
            entity_id = f"#nucleic-acid-type-{nucleic_acid.id}"
            if entity_id not in nucleic_acid_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(nucleic_acid, prefix="nucleic_acid_type_")
                    )
                )
                nucleic_acid_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Material",
                    "name": nucleic_acid.name or str(nucleic_acid),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_index_pool(pool):
            if pool is None:
                return None
            entity_id = f"#index-pool-{pool.id}"
            if entity_id not in index_pool_entities:
                properties = _build_property_values(
                    {
                        "index_pool_loaded": pool.loaded,
                        "index_pool_comment": pool.comment,
                    }
                )
                if pool.size:
                    properties.extend(
                        _build_property_values(
                            _extract_model_fields(pool.size, prefix="index_pool_size_")
                        )
                    )
                if pool.user:
                    user_name = getattr(pool.user, "full_name", None) or (
                        f"{pool.user.first_name} {pool.user.last_name}".strip()
                        or pool.user.email
                    )
                    _append_property(properties, "index_pool_user_name", user_name)
                    _append_property(
                        properties, "index_pool_user_email", pool.user.email
                    )
                library_barcodes = [library.barcode for library in pool.libraries.all()]
                sample_barcodes = [sample.barcode for sample in pool.samples.all()]
                if library_barcodes:
                    _append_property(
                        properties,
                        "index_pool_library_barcodes",
                        library_barcodes,
                    )
                if sample_barcodes:
                    _append_property(
                        properties,
                        "index_pool_sample_barcodes",
                        sample_barcodes,
                    )
                properties = _deduplicate_properties(properties)
                index_pool_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Pool",
                    "name": pool.name or f"Pool {pool.id}",
                    "additionalProperty": properties,
                }
            return entity_id

        def register_sequencer(sequencer):
            if sequencer is None:
                return None
            entity_id = f"#sequencer-{sequencer.id}"
            if entity_id not in sequencer_entities:
                properties = _deduplicate_properties(
                    _build_property_values(
                        _extract_model_fields(sequencer, prefix="sequencer_")
                    )
                )
                sequencer_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Instrument",
                    "name": sequencer.name or str(sequencer),
                    "additionalProperty": properties,
                }
            return entity_id

        def register_lane(lane):
            if lane is None:
                return None
            entity_id = f"#lane-{lane.id}"
            if entity_id not in lane_entities:
                properties = _build_property_values(
                    {
                        "lane_loading_concentration": lane.loading_concentration,
                        "lane_phix": lane.phix,
                        "lane_completed": lane.completed,
                        "lane_name": lane.name,
                    }
                )
                if lane.pool:
                    pool_id = register_index_pool(lane.pool)
                    if pool_id:
                        _append_property(properties, "associatedPool", {"@id": pool_id})
                lane_entities[entity_id] = {
                    "@id": entity_id,
                    "@type": "Lane",
                    "name": lane.name or f"Lane {lane.id}",
                    "additionalProperty": _deduplicate_properties(properties),
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
        if target_request_ids:
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
                        queryset=accessible_requests.filter(
                            id__in=target_request_ids
                        ).only("id", "name"),
                    ),
                    Prefetch("lanes", queryset=lane_queryset),
                )
                .distinct()
            )

            for flowcell in flowcells_qs:
                associated_requests = [
                    req.id
                    for req in flowcell.requests.all()
                    if req.id in requests_by_id
                ]
                if not associated_requests:
                    continue

                flowcell_base_data = _extract_model_fields(flowcell, prefix="flowcell_")
                flowcell_properties = _build_property_values(flowcell_base_data)

                sequencer_id = register_sequencer(flowcell.sequencer)
                if sequencer_id:
                    _append_property(
                        flowcell_properties, "hasInstrument", {"@id": sequencer_id}
                    )

                lane_refs = []
                for lane in flowcell.lanes.all():
                    lane_entity_id = register_lane(lane)
                    if lane_entity_id:
                        lane_refs.append({"@id": lane_entity_id})
                if lane_refs:
                    _append_property(flowcell_properties, "hasLane", lane_refs)

                _append_property(
                    flowcell_properties,
                    "flowcell_associated_requests",
                    [
                        requests_by_id[req_id].name
                        for req_id in associated_requests
                        if req_id in requests_by_id
                    ],
                )

                flowcell_entity_id = f"#flowcell-assay-{flowcell.id}"
                flowcell_entities[flowcell_entity_id] = {
                    "@id": flowcell_entity_id,
                    "@type": "Assay",
                    "name": f"Flowcell {flowcell.flowcell_id}",
                    "additionalProperty": _deduplicate_properties(flowcell_properties),
                }

                for req_id in associated_requests:
                    flowcells_by_request[req_id].append(flowcell_entity_id)

        samples_by_request = defaultdict(list)
        for entry in sample_data:
            samples_by_request[entry.request_id].append(entry)

        libraries_by_request = defaultdict(list)
        for entry in library_data:
            libraries_by_request[entry.request_id].append(entry)

        now_iso = timezone.now().isoformat()
        graph = []

        context_extensions = {
            "@base": "./",
            "Investigation": "https://w3id.org/isa/Investigation",
            "Study": "https://w3id.org/isa/Study",
            "Assay": "https://w3id.org/isa/Assay",
            "Material": "https://w3id.org/isa/Material",
            "Sample": "https://w3id.org/isa/Sample",
            "Library": "https://w3id.org/isa/Library",
            "Organism": "https://w3id.org/isa/Organism",
            "Protocol": "https://w3id.org/isa/Protocol",
            "Instrument": "https://w3id.org/isa/Instrument",
            "Pool": "https://w3id.org/isa/Pool",
            "Lane": "https://w3id.org/isa/Lane",
            "Thing": "https://schema.org/Thing",
            "PropertyValue": "https://schema.org/PropertyValue",
            "Person": "https://schema.org/Person",
            "Organization": "https://schema.org/Organization",
            "hasPart": {"@id": "https://schema.org/hasPart", "@type": "@id"},
            "hasAssay": {"@id": "https://w3id.org/isa/hasAssay", "@type": "@id"},
            "hasInput": {"@id": "https://w3id.org/isa/hasInput", "@type": "@id"},
            "hasOutput": {"@id": "https://w3id.org/isa/hasOutput", "@type": "@id"},
            "creator": {"@id": "https://schema.org/creator", "@type": "@id"},
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
        }

        graph.append(
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                "about": {"@id": "./"},
            }
        )

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

        dataset_entity = {
            "@id": "./",
            "@type": "Dataset",
            "name": "RO-Crate export for library preparation data",
            "dateCreated": now_iso,
            "conformsTo": {"@id": "https://w3id.org/isa/isa-model"},
            "hasPart": [],
            "additionalProperty": _deduplicate_properties(
                dataset_additional_properties
            ),
        }

        user_entities = {}

        for request_id in sorted(target_request_ids):
            request_obj = requests_by_id.get(request_id)
            if request_obj is None:
                continue

            investigation_id = f"#investigation-{request_id}"
            study_id = f"#study-{request_id}"
            dataset_entity["hasPart"].append({"@id": investigation_id})
            request_display_name = request_obj.name or f"Request {request_id}"

            request_data = _extract_model_fields(request_obj, prefix="request_")
            request_data.update(
                {
                    "request_user_full_name": request_obj.user.full_name
                    if request_obj.user
                    else None,
                    "request_user_email": request_obj.user.email
                    if request_obj.user
                    else None,
                    "request_cost_unit_name": request_obj.cost_unit.name
                    if request_obj.cost_unit
                    else None,
                    "request_pi_name": request_obj.user.pi.name
                    if getattr(request_obj.user, "pi", None)
                    else None,
                    "request_files": [
                        {"name": file.name, "path": file.file.name}
                        for file in request_obj.files.all()
                    ],
                    "request_deep_seq_request": request_obj.deep_seq_request.name
                    if request_obj.deep_seq_request
                    else None,
                }
            )

            investigation_properties = _build_property_values(request_data)
            cost_unit_id = register_cost_unit(request_obj.cost_unit)
            if cost_unit_id:
                _append_property(
                    investigation_properties, "costUnit", {"@id": cost_unit_id}
                )
            if request_obj.user:
                user_org_id = register_organization(request_obj.user.organization)
                if user_org_id:
                    _append_property(
                        investigation_properties,
                        "affiliatedOrganization",
                        {"@id": user_org_id},
                    )
                user_pi_id = register_principal_investigator(
                    getattr(request_obj.user, "pi", None)
                )
                if user_pi_id:
                    _append_property(
                        investigation_properties,
                        "principalInvestigator",
                        {"@id": user_pi_id},
                    )
            investigation_properties = _deduplicate_properties(investigation_properties)
            investigation_entity = {
                "@id": investigation_id,
                "@type": "Investigation",
                "name": request_display_name,
                "description": request_obj.description or "",
                "identifier": str(request_id),
                "dateCreated": _normalise_property_value(
                    getattr(request_obj, "create_time", None)
                ),
                "hasPart": [{"@id": study_id}],
                "additionalProperty": investigation_properties,
            }

            user_obj = getattr(request_obj, "user", None)
            if user_obj and user_obj.id not in user_entities:
                user_data = {
                    "user_first_name": user_obj.first_name,
                    "user_last_name": user_obj.last_name,
                    "user_email": user_obj.email,
                    "user_phone": user_obj.phone,
                    "user_is_pi": getattr(user_obj, "is_pi", False),
                    "user_is_staff": getattr(user_obj, "is_staff", False),
                }
                user_properties = _build_property_values(user_data)
                org_id = register_organization(user_obj.organization)
                if org_id:
                    _append_property(
                        user_properties, "affiliatedOrganization", {"@id": org_id}
                    )
                pi_id = register_principal_investigator(user_obj.pi)
                if pi_id:
                    _append_property(
                        user_properties, "principalInvestigator", {"@id": pi_id}
                    )
                user_properties = _deduplicate_properties(user_properties)

                user_entities[user_obj.id] = {
                    "@id": f"#person-{user_obj.id}",
                    "@type": "Person",
                    "name": user_obj.full_name,
                    "additionalProperty": user_properties,
                }

                investigation_entity["creator"] = {"@id": f"#person-{user_obj.id}"}

            study_properties = {
                "study_request_identifier": request_display_name,
                "study_samples_count": len(samples_by_request.get(request_id, [])),
                "study_libraries_count": len(libraries_by_request.get(request_id, [])),
            }

            study_entity = {
                "@id": study_id,
                "@type": "Study",
                "name": f"Study for {request_display_name}",
                "hasInput": [],
                "hasOutput": [],
                "hasAssay": [],
                "additionalProperty": _build_property_values(study_properties),
            }

            for sample_entry in samples_by_request.get(request_id, []):
                sample_material_id = f"#sample-material-{sample_entry.sample_id}"
                study_entity["hasInput"].append({"@id": sample_material_id})

                sample_model = samples_by_id.get(sample_entry.sample_id)
                sample_data = {}
                if sample_model:
                    sample_data.update(
                        _extract_model_fields(sample_model, prefix="sample_db_")
                    )
                sample_data.update(
                    _extract_model_fields(sample_entry, prefix="sample_mv_")
                )
                sample_properties = _build_property_values(sample_data)

                if sample_model:
                    organism_id = register_organism(sample_model.organism)
                    if organism_id:
                        _append_property(
                            sample_properties, "sample_organism", {"@id": organism_id}
                        )
                    protocol_id = register_protocol(sample_model.library_protocol)
                    if protocol_id:
                        _append_property(
                            sample_properties, "usesProtocol", {"@id": protocol_id}
                        )
                    library_type_id = register_library_type(sample_model.library_type)
                    if library_type_id:
                        _append_property(
                            sample_properties,
                            "sample_library_type",
                            {"@id": library_type_id},
                        )
                    read_length_id = register_read_length(sample_model.read_length)
                    if read_length_id:
                        _append_property(
                            sample_properties,
                            "sample_read_length",
                            {"@id": read_length_id},
                        )
                    index_type_id = register_index_type(sample_model.index_type)
                    if index_type_id:
                        _append_property(
                            sample_properties,
                            "sample_index_type",
                            {"@id": index_type_id},
                        )
                    nucleic_acid_id = register_nucleic_acid(
                        sample_model.nucleic_acid_type
                    )
                    if nucleic_acid_id:
                        _append_property(
                            sample_properties,
                            "sample_nucleic_acid_type",
                            {"@id": nucleic_acid_id},
                        )

                library_prep = library_preparations_by_sample.get(
                    sample_entry.sample_id
                )
                if library_prep:
                    sample_properties.extend(
                        _build_property_values(
                            _extract_model_fields(
                                library_prep, prefix="library_preparation_"
                            )
                        )
                    )

                sample_pooling = pooling_by_sample.get(sample_entry.sample_id)
                if sample_pooling:
                    sample_properties.extend(
                        _build_property_values(
                            _extract_model_fields(sample_pooling, prefix="pooling_")
                        )
                    )

                sample_pool_refs = sample_to_index_pools.get(sample_entry.sample_id, [])
                if sample_pool_refs:
                    _append_property(
                        sample_properties,
                        "associatedPool",
                        sample_pool_refs,
                    )
                sample_properties = _deduplicate_properties(sample_properties)
                sample_entity = {
                    "@id": sample_material_id,
                    "@type": ["Material", "Sample"],
                    "name": sample_entry.name,
                    "identifier": sample_entry.barcode,
                    "additionalProperty": sample_properties,
                }
                graph.append(sample_entity)

            for library_entry in libraries_by_request.get(request_id, []):
                library_material_id = f"#library-material-{library_entry.library_id}"
                assay_id = f"#library-assay-{library_entry.library_id}"

                study_entity["hasOutput"].append({"@id": library_material_id})
                study_entity["hasAssay"].append({"@id": assay_id})

                library_model = libraries_by_id.get(library_entry.library_id)
                library_material_data = {}
                if library_model:
                    library_material_data.update(
                        _extract_model_fields(library_model, prefix="library_db_")
                    )

                library_properties = _build_property_values(library_material_data)

                if library_model:
                    organism_id = register_organism(library_model.organism)
                    if organism_id:
                        _append_property(
                            library_properties,
                            "library_organism",
                            {"@id": organism_id},
                        )
                    protocol_id = register_protocol(library_model.library_protocol)
                    if protocol_id:
                        _append_property(
                            library_properties, "usesProtocol", {"@id": protocol_id}
                        )
                    library_type_id = register_library_type(library_model.library_type)
                    if library_type_id:
                        _append_property(
                            library_properties,
                            "library_library_type",
                            {"@id": library_type_id},
                        )
                    read_length_id = register_read_length(library_model.read_length)
                    if read_length_id:
                        _append_property(
                            library_properties,
                            "library_read_length",
                            {"@id": read_length_id},
                        )
                    index_type_id = register_index_type(library_model.index_type)
                    if index_type_id:
                        _append_property(
                            library_properties,
                            "library_index_type",
                            {"@id": index_type_id},
                        )

                library_pooling = pooling_by_library.get(library_entry.library_id)
                if library_pooling:
                    library_properties.extend(
                        _build_property_values(
                            _extract_model_fields(library_pooling, prefix="pooling_")
                        )
                    )

                library_pool_refs = library_to_index_pools.get(
                    library_entry.library_id, []
                )
                if library_pool_refs:
                    _append_property(
                        library_properties,
                        "associatedPool",
                        library_pool_refs,
                    )
                library_properties = _deduplicate_properties(library_properties)

                library_entity = {
                    "@id": library_material_id,
                    "@type": ["Material", "Library"],
                    "name": library_entry.name,
                    "identifier": library_entry.barcode,
                    "additionalProperty": library_properties,
                }

                assay_data = _extract_model_fields(library_entry, prefix="library_mv_")
                assay_entity = {
                    "@id": assay_id,
                    "@type": "Assay",
                    "name": f"Assay for library {library_entry.name}",
                    "hasOutput": {"@id": library_material_id},
                    "additionalProperty": _build_property_values(assay_data),
                }

                graph.append(library_entity)
                graph.append(assay_entity)

            flowcell_ids_for_request = flowcells_by_request.get(request_id, [])
            if flowcell_ids_for_request:
                seen_flowcells = set()
                for flowcell_entity_id in flowcell_ids_for_request:
                    if flowcell_entity_id in seen_flowcells:
                        continue
                    seen_flowcells.add(flowcell_entity_id)
                    study_entity["hasAssay"].append({"@id": flowcell_entity_id})
                _append_property(
                    study_entity["additionalProperty"],
                    "flowcell_assays",
                    [{"@id": flowcell_id} for flowcell_id in sorted(seen_flowcells)],
                )
            study_entity["additionalProperty"] = _deduplicate_properties(
                study_entity["additionalProperty"]
            )

            graph.append(investigation_entity)
            graph.append(study_entity)

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

        graph.insert(
            1,
            dataset_entity,
        )

        graph.extend(user_entities.values())

        ro_crate = {
            "@context": [
                "https://w3id.org/ro/crate/1.1/context",
                context_extensions,
            ],
            "@graph": graph,
        }

        return JsonResponse(
            ro_crate,
            json_dumps_params={"indent": 2},
            content_type="application/ld+json",
            safe=True,
        )


__all__ = ["GenerateROCrate"]
