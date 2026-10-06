from collections import defaultdict
from itertools import chain

from django.apps import apps
from django.db import transaction

from .models import IndexI5, IndexI7, IndexPair, IndexType

# Library/Sample statuses at or above this value mean the record reached
# "Sequencing" (5) or "Delivered" (6); negative statuses (failed/repeat) never count.
SEQUENCING_STATUS = 5


def _sequenced_records():
    """Library and Sample querysets restricted to records that reached Sequencing."""
    Library = apps.get_model("library", "Library")
    Sample = apps.get_model("sample", "Sample")
    return (
        Library.objects.filter(status__gte=SEQUENCING_STATUS),
        Sample.objects.filter(status__gte=SEQUENCING_STATUS),
    )


def index_type_is_used(index_type):
    """True if any record at Sequencing or higher references this IndexType, or
    one of its indices by sequence (also covers records whose IndexType FK is gone)."""
    i7 = list(index_type.indices_i7.values_list("index", flat=True))
    i5 = list(index_type.indices_i5.values_list("index", flat=True))
    for qs in _sequenced_records():
        if qs.filter(index_type=index_type).exists():
            return True
        if i7 and qs.filter(index_i7__in=i7).exists():
            return True
        if i5 and qs.filter(index_i5__in=i5).exists():
            return True
    return False


def index_is_used(index):
    """True if any record at Sequencing or higher carries this index's sequence.
    Works without an IndexType: the sequence string is the only link."""
    field = "index_i7" if isinstance(index, IndexI7) else "index_i5"
    return any(
        qs.filter(**{field: index.index}).exists() for qs in _sequenced_records()
    )


def index_pair_is_used(pair):
    """True if either constituent index of the pair is used by a sequenced record."""
    return any(
        idx is not None and index_is_used(idx) for idx in (pair.index1, pair.index2)
    )


def archive_index_pairs(queryset):
    """Archive IndexPairs, their constituent indices, and any IndexType left
    without an active pair. Shared by the admin actions and the delete fallback."""
    pair_ids = list(queryset.values_list("id", flat=True))
    type_ids = set(queryset.values_list("index_type", flat=True)) - {None}
    IndexPair.objects.filter(id__in=pair_ids).update(archived=True)
    IndexI7.objects.filter(indexpair__id__in=pair_ids).update(archived=True)
    IndexI5.objects.filter(indexpair__id__in=pair_ids).update(archived=True)
    for type_id in type_ids:
        if not IndexPair.objects.filter(index_type_id=type_id, archived=False).exists():
            IndexType.objects.filter(id=type_id).update(archived=True)


def archive_index_types(queryset):
    """Archive IndexTypes and cascade down: their pairs and indices. An index
    shared with a still-active IndexType stays active."""
    type_ids = list(queryset.values_list("id", flat=True))
    IndexType.objects.filter(id__in=type_ids).update(archived=True)
    archive_index_pairs(IndexPair.objects.filter(index_type_id__in=type_ids))
    for model in (IndexI7, IndexI5):
        model.objects.filter(index_type__id__in=type_ids).exclude(
            index_type__archived=False
        ).update(archived=True)


def index_has_used_pair(index):
    """True if a pair referencing this index is used (via its other index)."""
    field = "index1" if isinstance(index, IndexI7) else "index2"
    return any(
        index_pair_is_used(pair)
        for pair in IndexPair.objects.filter(**{field: index}).select_related(
            "index1", "index2"
        )
    )


@transaction.atomic
def delete_index_type(index_type):
    """Permanently delete an unused IndexType with its pairs, plus the indices
    that end up in no other IndexType and no other pair. Caller checks usage."""
    pairs = IndexPair.objects.filter(index_type=index_type)
    i7_ids = set(index_type.indices_i7.values_list("id", flat=True))
    i7_ids |= set(pairs.values_list("index1_id", flat=True))
    i5_ids = set(index_type.indices_i5.values_list("id", flat=True))
    i5_ids |= set(pairs.values_list("index2_id", flat=True))
    pairs.delete()
    index_type.delete()
    IndexI7.objects.filter(
        id__in=i7_ids, index_type__isnull=True, indexpair__isnull=True
    ).delete()
    IndexI5.objects.filter(
        id__in=i5_ids, index_type__isnull=True, indexpair__isnull=True
    ).delete()


@transaction.atomic
def delete_index(index):
    """Permanently delete an unused IndexI7/IndexI5 and the pairs built on it,
    so no half-empty pair is left behind. Caller checks usage."""
    field = "index1" if isinstance(index, IndexI7) else "index2"
    IndexPair.objects.filter(**{field: index}).delete()
    index.delete()


@transaction.atomic
def delete_index_pair(pair):
    """Permanently delete a pair and clean up its constituent indices.

    An index whose sequence is carried by a record at status >= Sequencing is
    archived instead of deleted. Otherwise it is deleted once no other pair and
    no other IndexType references it. The parent IndexType is archived when the
    pair was its last one.
    """
    type_id = pair.index_type_id
    i7 = pair.index1
    i5 = pair.index2
    pair.delete()
    for index, field in ((i7, "index1"), (i5, "index2")):
        if index is None:
            continue
        if index_is_used(index):
            if not index.archived:
                index.archived = True
                index.save(update_fields=["archived"])
            continue
        if IndexPair.objects.filter(**{field: index}).exists():
            continue
        other_types = index.index_type.all()
        if type_id:
            other_types = other_types.exclude(pk=type_id)
        if not other_types.exists():
            index.delete()
    if type_id and not IndexPair.objects.filter(index_type_id=type_id).exists():
        IndexType.objects.filter(id=type_id).update(archived=True)


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
