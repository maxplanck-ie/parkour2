from __future__ import annotations

from typing import Tuple
from collections.abc import Callable, Iterable, Sequence

from django.apps import apps
from django.db import transaction
from django.db.models import Q, QuerySet
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from django.utils import timezone

from common.mviews import refresh_batched

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")

ReadLength = apps.get_model("library_sample_shared", "ReadLength")
Organism = apps.get_model("library_sample_shared", "Organism")
LibraryProtocol = apps.get_model("library_sample_shared", "LibraryProtocol")
LibraryType = apps.get_model("library_sample_shared", "LibraryType")
IndexType = apps.get_model("library_sample_shared", "IndexType")
IndexI7 = apps.get_model("library_sample_shared", "IndexI7")
IndexI5 = apps.get_model("library_sample_shared", "IndexI5")
IndexPair = apps.get_model("library_sample_shared", "IndexPair")
NucleicAcidType = apps.get_model("sample", "NucleicAcidType")
Pool = apps.get_model("index_generator", "Pool")
Sequencer = apps.get_model("flowcell", "Sequencer")
Lane = apps.get_model("flowcell", "Lane")
Flowcell = apps.get_model("flowcell", "Flowcell")
LibraryPreparation = apps.get_model("library_preparation", "LibraryPreparation")
Pooling = apps.get_model("pooling", "Pooling")

DEFAULT_REFRESH_DELAY = 0.5

QC_APPROVED_STATUS = 2
FLOWCELL_LOADED_STATUS = 5


def _normalize_ids(values: Iterable[int] | None) -> tuple[int, ...]:
    if not values:
        return ()
    cleaned = {int(v) for v in values if v is not None}
    return tuple(sorted(cleaned))


def _query_ids(queryset: QuerySet, field: str = "id") -> Sequence[int]:
    return [
        int(pk)
        for pk in queryset.values_list(field, flat=True).distinct()
        if pk is not None
    ]


def _cache_related_ids(instance, libs: Iterable[int], samples: Iterable[int]) -> None:
    instance._denorm_library_ids = tuple(libs)
    instance._denorm_sample_ids = tuple(samples)


def _get_cached_ids(instance) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        getattr(instance, "_denorm_library_ids", ()),
        getattr(instance, "_denorm_sample_ids", ()),
    )


def _queue_refresh(
    library_ids: Iterable[int] | None = None,
    sample_ids: Iterable[int] | None = None,
    *,
    full: bool = False,
    delay: float = DEFAULT_REFRESH_DELAY,
) -> None:
    libs = _normalize_ids(library_ids)
    samples = _normalize_ids(sample_ids)

    def _callback() -> None:
        refresh_batched(
            concurrently=True,
            delay=delay,
            library_ids=libs,
            sample_ids=samples,
            full_refresh=full,
        )

    transaction.on_commit(_callback)


def _cache_previous_status(sender, instance) -> None:
    if not instance.pk:
        instance._previous_status = None
        return

    previous_status = (
        sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    )

    instance._previous_status = previous_status


@receiver(pre_save, sender=Library)
@receiver(pre_save, sender=Sample)
def cache_status_before_save(sender, instance, **kwargs):
    _cache_previous_status(sender, instance)


def _maybe_update_request_milestones(instance) -> None:
    previous_status = getattr(instance, "_previous_status", None)
    current_status = getattr(instance, "status", None)

    if current_status not in (QC_APPROVED_STATUS, FLOWCELL_LOADED_STATUS):
        return

    if previous_status == current_status:
        return

    timestamp_field = (
        "qc_completed_at"
        if current_status == QC_APPROVED_STATUS
        else "flowcell_loaded_at"
    )

    requests = list(
        instance.request.all().only("id", "qc_completed_at", "flowcell_loaded_at")
    )
    if not requests:
        return

    event_time = timezone.now()
    for request_obj in requests:
        if getattr(request_obj, timestamp_field) is not None:
            continue
        setattr(request_obj, timestamp_field, event_time)
        request_obj.save(update_fields=[timestamp_field])


def _collect_request_dependencies(
    request: Request,
) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(request.libraries.all())
    samples = _query_ids(request.samples.all())
    return libs, samples


def _collect_read_length(instance: ReadLength) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(Library.objects.filter(read_length_id=instance.pk))
    samples = _query_ids(Sample.objects.filter(read_length_id=instance.pk))
    return libs, samples


def _collect_organism(instance: Organism) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(Library.objects.filter(organism_id=instance.pk))
    samples = _query_ids(Sample.objects.filter(organism_id=instance.pk))
    return libs, samples


def _collect_library_protocol(
    instance: LibraryProtocol,
) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(Library.objects.filter(library_protocol_id=instance.pk))
    samples = _query_ids(Sample.objects.filter(library_protocol_id=instance.pk))
    return libs, samples


def _collect_library_type(instance: LibraryType) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(Library.objects.filter(library_type_id=instance.pk))
    samples = _query_ids(Sample.objects.filter(library_type_id=instance.pk))
    return libs, samples


def _collect_index_type(instance: IndexType) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(Library.objects.filter(index_type_id=instance.pk))
    samples = _query_ids(Sample.objects.filter(index_type_id=instance.pk))
    return libs, samples


def _collect_index_i7(instance: IndexI7) -> tuple[Sequence[int], Sequence[int]]:
    index_value = instance.index
    libs = _query_ids(Library.objects.filter(index_i7=index_value))
    samples = _query_ids(Sample.objects.filter(index_i7=index_value))
    return libs, samples


def _collect_index_i5(instance: IndexI5) -> tuple[Sequence[int], Sequence[int]]:
    index_value = instance.index
    libs = _query_ids(Library.objects.filter(index_i5=index_value))
    samples = _query_ids(Sample.objects.filter(index_i5=index_value))
    return libs, samples


def _collect_index_pair(instance: IndexPair) -> tuple[Sequence[int], Sequence[int]]:
    index_i7 = getattr(instance.index1, "index", None)
    index_i5 = getattr(instance.index2, "index", None)
    if not index_i7 and not index_i5:
        return (), ()

    library_filter = Q()
    sample_filter = Q()
    if instance.index_type_id:
        library_filter &= Q(index_type_id=instance.index_type_id)
        sample_filter &= Q(index_type_id=instance.index_type_id)
    if index_i7:
        library_filter &= Q(index_i7=index_i7)
        sample_filter &= Q(index_i7=index_i7)
    if index_i5:
        library_filter &= Q(index_i5=index_i5)
        sample_filter &= Q(index_i5=index_i5)

    libs = _query_ids(Library.objects.filter(library_filter))
    samples = _query_ids(Sample.objects.filter(sample_filter))
    return libs, samples


def _collect_nucleic_acid_type(
    instance: NucleicAcidType,
) -> tuple[Sequence[int], Sequence[int]]:
    samples = _query_ids(Sample.objects.filter(nucleic_acid_type_id=instance.pk))
    return (), samples


def _collect_pool(instance: Pool) -> tuple[Sequence[int], Sequence[int]]:
    libs = _query_ids(instance.libraries.all())
    samples = _query_ids(instance.samples.all())
    return libs, samples


def _collect_flowcells(
    flowcells: Iterable[Flowcell],
) -> tuple[Sequence[int], Sequence[int]]:
    flowcell_ids = [fc.id for fc in flowcells if fc.id]
    if not flowcell_ids:
        return (), ()

    pool_ids = _query_ids(
        Lane.objects.filter(flowcell__id__in=flowcell_ids).exclude(
            pool_id__isnull=True
        ),
        field="pool_id",
    )
    request_ids = [
        int(request_id)
        for request_id in Flowcell.objects.filter(id__in=flowcell_ids)
        .values_list("requests__id", flat=True)
        .distinct()
        if request_id is not None
    ]

    libs = set()
    samples = set()

    if pool_ids:
        libs.update(_query_ids(Library.objects.filter(pool__id__in=pool_ids)))
        samples.update(_query_ids(Sample.objects.filter(pool__id__in=pool_ids)))

    if request_ids:
        libs.update(_query_ids(Library.objects.filter(request__id__in=request_ids)))
        samples.update(_query_ids(Sample.objects.filter(request__id__in=request_ids)))

    return tuple(sorted(libs)), tuple(sorted(samples))


def _collect_sequencer(instance: Sequencer) -> tuple[Sequence[int], Sequence[int]]:
    flowcells = Flowcell.objects.filter(sequencer_id=instance.pk)
    return _collect_flowcells(flowcells)


def _collect_lane(instance: Lane) -> tuple[Sequence[int], Sequence[int]]:
    libs = set()
    samples = set()

    if instance.pool_id:
        libs.update(_query_ids(Library.objects.filter(pool__id=instance.pool_id)))
        samples.update(_query_ids(Sample.objects.filter(pool__id=instance.pool_id)))

    flowcells = instance.flowcell.all()
    flowcell_libs, flowcell_samples = _collect_flowcells(flowcells)
    libs.update(flowcell_libs)
    samples.update(flowcell_samples)

    return tuple(sorted(libs)), tuple(sorted(samples))


def _collect_flowcell(instance: Flowcell) -> tuple[Sequence[int], Sequence[int]]:
    return _collect_flowcells([instance])


def _collect_library_preparation(
    instance: LibraryPreparation,
) -> tuple[Sequence[int], Sequence[int]]:
    sample_id = instance.sample_id
    return (), (sample_id,) if sample_id else ()


def _collect_pooling(instance: Pooling) -> tuple[Sequence[int], Sequence[int]]:
    libs = (instance.library_id,) if instance.library_id else ()
    samples = (instance.sample_id,) if instance.sample_id else ()
    return libs, samples


RELATED_COLLECTORS: dict[type, Callable] = {
    ReadLength: _collect_read_length,
    Organism: _collect_organism,
    LibraryProtocol: _collect_library_protocol,
    LibraryType: _collect_library_type,
    IndexType: _collect_index_type,
    IndexI7: _collect_index_i7,
    IndexI5: _collect_index_i5,
    IndexPair: _collect_index_pair,
    NucleicAcidType: _collect_nucleic_acid_type,
    Pool: _collect_pool,
    Sequencer: _collect_sequencer,
    Lane: _collect_lane,
    Flowcell: _collect_flowcell,
    LibraryPreparation: _collect_library_preparation,
    Pooling: _collect_pooling,
}


def _collect_and_cache(
    instance, collector: Callable
) -> tuple[Sequence[int], Sequence[int]]:
    libs, samples = collector(instance)
    _cache_related_ids(instance, libs, samples)
    return libs, samples


# --- Request ---
@receiver(pre_delete, sender=Request)
def cache_request_before_delete(sender, instance, **kwargs):
    _collect_and_cache(instance, _collect_request_dependencies)


@receiver(post_save, sender=Request)
def on_request_save(sender, instance, created, **kwargs):
    libs, samples = _collect_request_dependencies(instance)
    _queue_refresh(library_ids=libs, sample_ids=samples)


@receiver(post_delete, sender=Request)
def on_request_delete(sender, instance, **kwargs):
    libs, samples = _get_cached_ids(instance)
    _queue_refresh(library_ids=libs, sample_ids=samples, full=False)


# --- Library ---
@receiver(post_save, sender=Library)
def on_library_save(sender, instance, **kwargs):
    _queue_refresh(library_ids=[instance.pk])
    _maybe_update_request_milestones(instance)


@receiver(post_delete, sender=Library)
def on_library_delete(sender, instance, **kwargs):
    _queue_refresh(library_ids=[instance.pk])


# --- Sample ---
@receiver(post_save, sender=Sample)
def on_sample_save(sender, instance, **kwargs):
    _queue_refresh(sample_ids=[instance.pk])
    _maybe_update_request_milestones(instance)


@receiver(post_delete, sender=Sample)
def on_sample_delete(sender, instance, **kwargs):
    _queue_refresh(sample_ids=[instance.pk])


# --- Request m2m ---
@receiver(m2m_changed, sender=Request.libraries.through)
def on_request_libraries_m2m(sender, instance, action, pk_set, **kwargs):
    if action == "pre_clear":
        _cache_related_ids(instance, _query_ids(instance.libraries.all()), ())
        return

    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    if action == "post_clear":
        libs, _ = _get_cached_ids(instance)
        _queue_refresh(library_ids=libs)
        return

    if pk_set:
        _queue_refresh(library_ids=pk_set)


@receiver(m2m_changed, sender=Request.samples.through)
def on_request_samples_m2m(sender, instance, action, pk_set, **kwargs):
    if action == "pre_clear":
        _cache_related_ids(instance, (), _query_ids(instance.samples.all()))
        return

    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    if action == "post_clear":
        _, samples = _get_cached_ids(instance)
        _queue_refresh(sample_ids=samples)
        return

    if pk_set:
        _queue_refresh(sample_ids=pk_set)


# --- Related models ---
@receiver(
    pre_delete,
    sender=ReadLength,
)
@receiver(pre_delete, sender=Organism)
@receiver(pre_delete, sender=LibraryProtocol)
@receiver(pre_delete, sender=LibraryType)
@receiver(pre_delete, sender=IndexType)
@receiver(pre_delete, sender=IndexI7)
@receiver(pre_delete, sender=IndexI5)
@receiver(pre_delete, sender=IndexPair)
@receiver(pre_delete, sender=NucleicAcidType)
@receiver(pre_delete, sender=Pool)
@receiver(pre_delete, sender=Sequencer)
@receiver(pre_delete, sender=Lane)
@receiver(pre_delete, sender=Flowcell)
@receiver(pre_delete, sender=LibraryPreparation)
@receiver(pre_delete, sender=Pooling)
def cache_related_model_before_delete(sender, instance, **kwargs):
    collector = RELATED_COLLECTORS.get(sender)
    if collector:
        _collect_and_cache(instance, collector)


@receiver(
    post_save,
    sender=ReadLength,
)
@receiver(post_save, sender=Organism)
@receiver(post_save, sender=LibraryProtocol)
@receiver(post_save, sender=LibraryType)
@receiver(post_save, sender=IndexType)
@receiver(post_save, sender=IndexI7)
@receiver(post_save, sender=IndexI5)
@receiver(post_save, sender=IndexPair)
@receiver(post_save, sender=NucleicAcidType)
@receiver(post_save, sender=Pool)
@receiver(post_save, sender=Sequencer)
@receiver(post_save, sender=Lane)
@receiver(post_save, sender=Flowcell)
@receiver(post_save, sender=LibraryPreparation)
@receiver(post_save, sender=Pooling)
def on_related_model_save(sender, instance, **kwargs):
    collector = RELATED_COLLECTORS.get(sender)
    if not collector:
        return
    libs, samples = collector(instance)
    _queue_refresh(library_ids=libs, sample_ids=samples)


@receiver(
    post_delete,
    sender=ReadLength,
)
@receiver(post_delete, sender=Organism)
@receiver(post_delete, sender=LibraryProtocol)
@receiver(post_delete, sender=LibraryType)
@receiver(post_delete, sender=IndexType)
@receiver(post_delete, sender=IndexI7)
@receiver(post_delete, sender=IndexI5)
@receiver(post_delete, sender=IndexPair)
@receiver(post_delete, sender=NucleicAcidType)
@receiver(post_delete, sender=Pool)
@receiver(post_delete, sender=Sequencer)
@receiver(post_delete, sender=Lane)
@receiver(post_delete, sender=Flowcell)
@receiver(post_delete, sender=LibraryPreparation)
@receiver(post_delete, sender=Pooling)
def on_related_model_delete(sender, instance, **kwargs):
    libs, samples = _get_cached_ids(instance)
    _queue_refresh(library_ids=libs, sample_ids=samples)
