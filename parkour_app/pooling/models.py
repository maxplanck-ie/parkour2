from django.db import models

from common.models import DateTimeMixin
from library.models import Library
from sample.models import Sample


class Pooling(DateTimeMixin):
    library = models.OneToOneField(
        Library,
        verbose_name='Library',
        null=True,
        blank=True
    )

    sample = models.OneToOneField(
        Sample,
        verbose_name='Sample',
        null=True,
        blank=True
    )

    concentration_c1 = models.FloatField(
        'Concentration C1',
        null=True,
        blank=True
    )

    comment = models.TextField(verbose_name='Comment',blank=True)

    class Meta:
        verbose_name = 'Pooling'
        verbose_name_plural = 'Pooling'

    def __str__(self):
        obj = self.library if self.library else self.sample
        # return '%s (%s)' % (obj.name, obj.pool.get())
        return f'{obj.name} ({obj.barcode})'
