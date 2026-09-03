from collections import defaultdict
from itertools import chain

from django.apps import apps

from .models import IndexType


def get_indices_ids(obj):
    """Get Index I7/I5 ids for a given library/sample."""

    try:
        index_type = IndexType.objects.filter(archived=False).get(pk=obj.index_type.pk)
        index_i7 = index_type.indices_i7.get(index=obj.index_i7)
        index_i7_id = index_i7.index_id
    except Exception:
        index_i7_id = ""

    try:
        index_type = IndexType.objects.filter(archived=False).get(pk=obj.index_type.pk)
        index_i5 = index_type.indices_i5.get(index=obj.index_i5)
        index_i5_id = index_i5.index_id
    except Exception:
        index_i5_id = ""

    return index_i7_id, index_i5_id


def _well_label(index):
    well_index = index % 96
    return f"{chr(65 + well_index % 8)}{well_index // 8 + 1}"


def compute_plate_coords(request_names):
    """Bulk-compute Plate Coord (A1..H12) for every library/sample record
    across the given request names, in 2 queries total.

    Within each request name, libraries and samples are combined and
    ranked together by barcode (barcodes are fixed-width and globally
    sortable; pk is an extra tie-break for the rare case of duplicate
    legacy barcodes), then the rank is mapped to a well label (index % 96).
    Mirrors the "Plate Coord" column computed client-side in
    librariesAndSamplesView.vue, which groups by request_name across both
    record types before assigning coordinates.

    Keyed by (request_name, record_type, pk) rather than by barcode. New
    barcodes are unique (BarcodeCounter), but older ones aren't: a past
    BarcodeCounter bug left two Sample rows in a 2019 request sharing the
    same barcode, and that historical data is still in the database today.
    Keying by barcode alone would collapse rows like those onto a single
    shared coord.

    Returns {(request_name, "library"|"sample", pk): plate_coord}.
    """
    CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")
    CompleteSampleData = apps.get_model("sample", "CompleteSampleData")

    library_rows = CompleteLibraryData.objects.filter(
        request_name__in=request_names
    ).values_list("request_name", "barcode", "library_id")
    sample_rows = CompleteSampleData.objects.filter(
        request_name__in=request_names
    ).values_list("request_name", "barcode", "sample_id")

    grouped = defaultdict(list)
    for request_name, barcode, pk in library_rows:
        grouped[request_name].append((barcode, "library", pk))
    for request_name, barcode, pk in sample_rows:
        grouped[request_name].append((barcode, "sample", pk))

    result = {}
    for request_name, records in grouped.items():
        records.sort()
        for index, (_barcode, record_type, pk) in enumerate(records):
            result[(request_name, record_type, pk)] = _well_label(index)
    return result


def compute_plate_coord(request_name, record_type, pk):
    """Single-record convenience wrapper around compute_plate_coords."""
    return compute_plate_coords([request_name])[(request_name, record_type, pk)]


def move_other_to_end(data):
    """Move 'Other' option to the end of the list."""
    result = []
    result.extend(data)

    other = [x for x in result if x["name"] == "Other"]
    if other:
        index = result.index(other[0])
        result.append(result.pop(index))

    return result
