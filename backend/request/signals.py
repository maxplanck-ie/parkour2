from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.apps import apps

from common.mviews import refresh_immediately_non_blocking

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")

ReadLength = apps.get_model("library_sample_shared", "ReadLength")
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


# --- Request ---
@receiver(post_save, sender=Request)
@receiver(post_delete, sender=Request)
def on_request_change(sender, instance, **kwargs):
    transaction.on_commit(lambda: refresh_immediately_non_blocking(concurrently=True))


# --- Library ---
@receiver(post_save, sender=Library)
@receiver(post_delete, sender=Library)
def on_library_change(sender, instance, **kwargs):
    transaction.on_commit(lambda: refresh_immediately_non_blocking(concurrently=True))


# --- Sample ---
@receiver(post_save, sender=Sample)
@receiver(post_delete, sender=Sample)
def on_sample_change(sender, instance, **kwargs):
    transaction.on_commit(lambda: refresh_immediately_non_blocking(concurrently=True))


# --- m2m changes ---
@receiver(m2m_changed, sender=Request.libraries.through)
@receiver(m2m_changed, sender=Request.samples.through)
def on_request_m2m_change(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        transaction.on_commit(
            lambda: refresh_immediately_non_blocking(concurrently=True)
        )


# --- Other shared models ---
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
@receiver(post_save, sender=NucleicAcidType)
@receiver(post_delete, sender=NucleicAcidType)
@receiver(post_save, sender=Pool)
@receiver(post_delete, sender=Pool)
@receiver(post_save, sender=Sequencer)
@receiver(post_delete, sender=Sequencer)
@receiver(post_save, sender=Lane)
@receiver(post_delete, sender=Lane)
@receiver(post_save, sender=Flowcell)
@receiver(post_delete, sender=Flowcell)
@receiver(post_save, sender=LibraryPreparation)
@receiver(post_delete, sender=LibraryPreparation)
@receiver(post_save, sender=Pooling)
@receiver(post_delete, sender=Pooling)
def on_any_other_model_change(sender, instance, **kwargs):
    transaction.on_commit(lambda: refresh_immediately_non_blocking(concurrently=True))
