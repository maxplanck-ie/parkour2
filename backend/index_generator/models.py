import itertools

from common.models import DateTimeMixin
from django.conf import settings
from django.db import models
from library.models import Library
from sample.models import Sample

from math import log, floor
from decimal import Decimal

class PoolSize(models.Model):
    sequencer = models.ForeignKey('flowcell.Sequencer',
                                  verbose_name='Sequencer',
                                  null=True,
                                  on_delete=models.SET_NULL)
    short_name = models.CharField("Name", max_length=20, blank=False)
    size = models.PositiveSmallIntegerField("Size (in million reads)")
    lanes = models.PositiveSmallIntegerField("Number of Lanes")
    cycles = models.PositiveSmallIntegerField("Number of cycles")
    read_lengths = models.ManyToManyField('library_sample_shared.ReadLength', verbose_name='read lengths', related_name='pool_size',)
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        ordering = ["sequencer", "size", "cycles"]
        constraints = [
            models.UniqueConstraint(fields=['sequencer', 'size', 'cycles', 'lanes', 'archived'],
                                    name='unique_pool_size')
        ]

    def __str__(self):
        # size = Decimal(self.size)
        # prefixes = ['M', 'G', 'T', 'P']
        # k = Decimal(1000)
        # magnitude = int(floor(log(size, k)))
        # return f"{self.sequencer} - {self.lanes}×{size / k**Decimal(magnitude)}{prefixes[magnitude]}, {self.cycles}c"
        return  f"{self.sequencer} - {self.short_name}"

    @property
    def name(self):
        return self.__str__()

    @property
    def multiplier(self):
        return self.lanes


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username="deleted")[0]


class Pool(DateTimeMixin):
    name = models.CharField("Name", max_length=100, blank=True, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="User",
        on_delete=models.SET(get_sentinel_user),
    )
    size = models.ForeignKey(
        PoolSize, verbose_name="Size", on_delete=models.SET_NULL, null=True
    )
    loaded = models.PositiveSmallIntegerField("Loaded", default=0, blank=True)
    libraries = models.ManyToManyField(Library, related_name="pool", blank=True)
    samples = models.ManyToManyField(Sample, related_name="pool", blank=True)
    comment = models.TextField(verbose_name="Comment", blank=True)
    archived = models.BooleanField("Archived", default=False)

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
        records = list(itertools.chain(self.samples.all(), self.libraries.all()))
        return sum(x.sequencing_depth for x in records)

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created and not self.name:
            # Update the pool name after receiving a Pool id
            self.name = f"Pool_{self.pk}"
            self.save()
