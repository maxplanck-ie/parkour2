import itertools

from django.db import models
from django.conf import settings

from common.models import DateTimeMixin
from library.models import Library
from sample.models import Sample

class PoolSize(models.Model):
    multiplier = models.PositiveSmallIntegerField('Multiplier', default=1)
    size = models.PositiveSmallIntegerField('Size')
    obsolete = models.PositiveIntegerField("Obsolete", default=1)

    class Meta:
        ordering = ['multiplier', 'size']

    def __str__(self):
        return f'{self.multiplier}x{self.size}'

    @property
    def name(self):
        return f'{self.multiplier}x{self.size}'


class Pool(DateTimeMixin):
    name = models.CharField('Name', max_length=100, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User')
    size = models.ForeignKey(PoolSize, verbose_name='Size')
    loaded = models.PositiveSmallIntegerField('Loaded', default=0, blank=True)
    libraries = models.ManyToManyField(
        Library, related_name='pool', blank=True)
    samples = models.ManyToManyField(
        Sample, related_name='pool', blank=True)
    comment = models.TextField(verbose_name='Comment', blank=True)

    # def get_size(self):
    #     size = 0
    #     for library in self.libraries.all():
    #         size += library.sequencing_depth
    #     for sample in self.samples.all():
    #         size += sample.sequencing_depth
    #     return size

    def __str__(self):
        return self.name

    @property
    def total_sequencing_depth(self):
        records = list(itertools.chain(
            self.samples.all(), self.libraries.all()))
        return sum([x.sequencing_depth for x in records])

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created:
            # Update the pool name after receiving a Pool id
            self.name = f'Pool_{self.pk}'
            self.save()
