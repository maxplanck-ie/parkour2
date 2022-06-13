import itertools

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

from common.models import DateTimeMixin, CostUnit
from library.models import Library
from sample.models import Sample


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


class FileRequest(models.Model):
    name = models.CharField('Name', max_length=200)
    file = models.FileField(upload_to='request_files/%Y/%m/%d/')

    def __str__(self):
        return self.name


class Request(DateTimeMixin):
    name = models.CharField('Name', max_length=100, blank=True)
    description = models.TextField()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='User',
        on_delete=models.SET(get_sentinel_user),
    )

    cost_unit = models.ForeignKey(
        CostUnit,
        verbose_name='Cost Unit',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    libraries = models.ManyToManyField(
        Library,
        related_name='request',
        blank=True,
    )

    samples = models.ManyToManyField(
        Sample,
        related_name='request',
        blank=True,
    )

    files = models.ManyToManyField(
        FileRequest,
        related_name='request',
        blank=True,
    )

    deep_seq_request = models.FileField(
        verbose_name='Deep Sequencing Request',
        upload_to='deep_sequencing_requests/%Y/%m/%d/',
        blank=True,
        null=True,
    )

    samples_submitted = models.BooleanField(
        verbose_name='Samples Submitted',
        default=False,
    )

    sequenced = models.BooleanField(
        verbose_name='Sequenced',
        default=False,
    )

    def __str__(self):
        return self.name

    @property
    def records(self):
        return list(itertools.chain(self.samples.all(), self.libraries.all()))

    @property
    def total_sequencing_depth(self):
        return sum([x.sequencing_depth for x in self.records])

    @property
    def total_records_count(self):
        return len(self.records)

    @property
    def statuses(self):
        return [x.status for x in self.records]

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created:
            # Set name after getting an id
            self.name = f'{self.id}_{self.user.last_name}'
            if self.user.pi:
                self.name += '_' + self.user.pi.name
            self.save()

    def delete(self, *args, **kwargs):
        # Delete all libraries and samples
        self.libraries.all().delete()
        self.samples.all().delete()

        # Delete all files
        self.files.all().delete()

        super().delete(*args, **kwargs)
