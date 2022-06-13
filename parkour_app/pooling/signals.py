from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from sample.models import Sample
from index_generator.models import Pool
from library_preparation.models import LibraryPreparation
from .models import Pooling


@receiver(m2m_changed, sender=Pool.libraries.through)
def update_libraries_create_pooling_obj(sender, instance, action, **kwargs):
    """
    When a library is added to a pool, set its is_pooled to True, and
    for each library create a Pooling object.
    """
    if action == 'post_add':
        instance.libraries.all().update(is_pooled=True)

        # TODO: maybe there is a better way to create multiple objects at once
        for library in instance.libraries.all():
            obj, created = Pooling.objects.get_or_create(library=library)
            if created:
                obj.save()


@receiver(post_save, sender=Sample)
def create_pooling_objects_sample(sender, instance, **kwargs):
    """
    When a sample passes the quality check and reaches the status 3,
    create a Pooling object for it.
    """

    # Ignore the signal if a sample is not in a pool yet
    if not instance.is_pooled:
        return

    try:
        lib_prep_object = LibraryPreparation.objects.get(sample=instance)
    except LibraryPreparation.DoesNotExist:
        lib_prep_object = None

    if lib_prep_object and instance.status == 3:
        # If a sample has an associated Library Preparation object and
        # passes the quality check, create a Pooling object for the sample
        obj, created = Pooling.objects.get_or_create(sample=instance)
        if created:
            obj.save()
