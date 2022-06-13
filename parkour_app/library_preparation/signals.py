from django.db.models import F, Func, Value
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from index_generator.models import Pool
from .models import LibraryPreparation


@receiver(m2m_changed, sender=Pool.samples.through)
def update_samples(sender, instance, action, **kwargs):
    """
    When a sample is added to a pool, set its is_pooled and is_converted
    to True, update the barcode, and for each sample in the pool create a
    LibraryPreparation object.
    """
    if action == 'post_add':
        instance.samples.all().update(
            is_pooled=True,
            is_converted=True,
            barcode=Func(
                F('barcode'),
                Value('S'), Value('L'),
                function='replace',
            ),
        )

        # TODO: maybe there is a better way to create multiple objects at once
        for sample in instance.samples.all():
            obj, created = LibraryPreparation.objects.get_or_create(
                sample=sample)
            if created:
                obj.save()
