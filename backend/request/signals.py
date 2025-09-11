from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.apps import apps

from common.mviews import (
    schedule_refresh_complete_data_materialized_views,
    schedule_refresh_library_mv,
    schedule_refresh_sample_mv,
)


Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")

# Other dependent models referenced by the MVs
ReadLength = apps.get_model("library_sample_shared", "ReadLength")
LibraryProtocol = apps.get_model("library_sample_shared", "LibraryProtocol")
LibraryType = apps.get_model("library_sample_shared", "LibraryType")
IndexType = apps.get_model("library_sample_shared", "IndexType")
IndexI7 = apps.get_model("library_sample_shared", "IndexI7")
IndexI5 = apps.get_model("library_sample_shared", "IndexI5")
IndexPair = apps.get_model("library_sample_shared", "IndexPair")

NucleicAcidType = apps.get_model("sample", "NucleicAcidType")
LibraryPreparation = apps.get_model("library_preparation", "LibraryPreparation")

Pool = apps.get_model("index_generator", "Pool")

Sequencer = apps.get_model("flowcell", "Sequencer")
Lane = apps.get_model("flowcell", "Lane")
Flowcell = apps.get_model("flowcell", "Flowcell")


def _schedule_refresh():
    # Non-blocking background refresh after commit
    schedule_refresh_complete_data_materialized_views(concurrently=True)


def _schedule_refresh_lib():
    schedule_refresh_library_mv(concurrently=True)


def _schedule_refresh_sample():
    schedule_refresh_sample_mv(concurrently=True)


@receiver(post_save, sender=Request)
def on_request_save(sender, instance, created, **kwargs):
    _schedule_refresh()


@receiver(post_delete, sender=Request)
def on_request_delete(sender, instance, **kwargs):
    _schedule_refresh()


@receiver(post_save, sender=Library)
def on_library_save(sender, instance, created, **kwargs):
    _schedule_refresh_lib()


@receiver(post_delete, sender=Library)
def on_library_delete(sender, instance, **kwargs):
    _schedule_refresh_lib()


@receiver(post_save, sender=Sample)
def on_sample_save(sender, instance, created, **kwargs):
    _schedule_refresh_sample()


@receiver(post_delete, sender=Sample)
def on_sample_delete(sender, instance, **kwargs):
    _schedule_refresh_sample()


# Listen to M2M changes to link/unlink libraries/samples to requests
@receiver(m2m_changed, sender=Request.libraries.through)
def on_request_libraries_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _schedule_refresh_lib()


@receiver(m2m_changed, sender=Request.samples.through)
def on_request_samples_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _schedule_refresh_sample()


# library_sample_shared changes (indexes, protocols, read lengths, etc.)
@receiver(post_save, sender=ReadLength)
@receiver(post_delete, sender=ReadLength)
@receiver(post_save, sender=LibraryProtocol)
@receiver(post_delete, sender=LibraryProtocol)
@receiver(post_save, sender=LibraryType)
@receiver(post_delete, sender=LibraryType)
@receiver(post_save, sender=IndexType)
@receiver(post_delete, sender=IndexType)
@receiver(post_save, sender=IndexI7)
@receiver(post_delete, sender=IndexI7)
@receiver(post_save, sender=IndexI5)
@receiver(post_delete, sender=IndexI5)
@receiver(post_save, sender=IndexPair)
@receiver(post_delete, sender=IndexPair)
def on_library_shared_change(sender, instance, **kwargs):
    _schedule_refresh()


# sample side aux models
@receiver(post_save, sender=NucleicAcidType)
@receiver(post_delete, sender=NucleicAcidType)
def on_sample_aux_change(sender, instance, **kwargs):
    _schedule_refresh_sample()


# library preparation impacts sample MV
@receiver(post_save, sender=LibraryPreparation)
@receiver(post_delete, sender=LibraryPreparation)
def on_library_preparation_change(sender, instance, **kwargs):
    _schedule_refresh_sample()


# index generator: pool name/links impact pools in MVs
@receiver(post_save, sender=Pool)
@receiver(post_delete, sender=Pool)
def on_pool_change(sender, instance, **kwargs):
    _schedule_refresh()


@receiver(m2m_changed, sender=Pool.libraries.through)
def on_pool_libraries_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _schedule_refresh_lib()


@receiver(m2m_changed, sender=Pool.samples.through)
def on_pool_samples_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _schedule_refresh_sample()


# flowcell: sequencer, lanes, flowcell/lanes relations impact sequencer and flowcell arrays
@receiver(post_save, sender=Sequencer)
@receiver(post_delete, sender=Sequencer)
@receiver(post_save, sender=Lane)
@receiver(post_delete, sender=Lane)
@receiver(post_save, sender=Flowcell)
@receiver(post_delete, sender=Flowcell)
def on_flowcell_related_change(sender, instance, **kwargs):
    _schedule_refresh()


@receiver(m2m_changed, sender=Flowcell.lanes.through)
def on_flowcell_lanes_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _schedule_refresh()
