from django.db import models

from common.models import DateTimeMixin
from sample.models import Sample


class LibraryPreparation(DateTimeMixin):
    sample = models.OneToOneField(Sample, verbose_name='Sample')

    starting_amount = models.FloatField(
        'Starting Amount',
        null=True,
        blank=True,
    )

    spike_in_description = models.TextField(
        'Spike-in Description',
        null=True,
        blank=True,
    )

    spike_in_volume = models.FloatField(
        'Spike-in Volume',
        null=True,
        blank=True,
    )

    pcr_cycles = models.IntegerField(
        'PCR Cycles',
        null=True,
        blank=True,
    )

    concentration_library = models.FloatField(
        'Concentration Library',
        null=True,
        blank=True,
    )

    mean_fragment_size = models.IntegerField(
        'Mean Fragment Size',
        null=True,
        blank=True,
    )

    nM = models.FloatField(
        'nM',
        null=True,
        blank=True,
    )

    qpcr_result = models.FloatField(
        'qPCR Result',
        null=True,
        blank=True,
    )

    comments = models.TextField(
        'Comments',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Library Preparation'
        verbose_name_plural = 'Library Preparation'

    def __str__(self):
        # return '%s (Request: %s)' % (self.sample.name,
        #                              self.sample.request.get())
        return '{} ({})'.format(self.sample.name, self.sample.barcode)
