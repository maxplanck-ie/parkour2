import itertools

from common.models import CostUnit, User, DateTimeMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from library.models import Library
from sample.models import Sample
from index_generator.models import PoolSize


def get_sentinel_user():
    return get_user_model().objects.get_or_create(email="deleted.user@example.com",
                                                  first_name='Deleted',
                                                  last_name='User')[0]

def filepaths_default():
    return {"data": None, "metadata": None}


def metapaths_default():
    return {"nothing": None}


def approval_default():
    return {
        "TIMESTAMP": None,
        "TOKEN": None,
        "REMOTE_ADDR": None,
        "REMOTE_PORT": None,
        "HTTP_USER_AGENT": None,
        "HTTP_ACCEPT": None,
        "HTTP_ACCEPT_ENCODING": None,
        "HTTP_ACCEPT_LANGUAGE": None,
        "HTTP_FORWARDED": None,
        "HTTP_X_FORWARDED_FOR": None,
        "OIDC_ID": None,
        "EMAIL": None
    }



class FileRequest(models.Model):
    name = models.CharField("Name", max_length=200)
    file = models.FileField(upload_to="request_files/%Y/%m/%d/", max_length=200)

    def __str__(self):
        return self.name


class Request(DateTimeMixin):
    name = models.CharField("Name", max_length=100, blank=True)
    description = models.TextField(blank=True)
    token = models.CharField("Token",
                             max_length=50,
                             blank=True,
                             null=True,
                             unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="User",
        on_delete=models.SET(get_sentinel_user),
    )

    pi = models.ForeignKey(
        User,
        verbose_name="PI",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name = 'request_pi'
    )

    cost_unit = models.ForeignKey(
        CostUnit,
        verbose_name="Cost Unit",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    bioinformatician = models.ForeignKey(
        User,
        verbose_name="Bioinformatician",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name = 'request_bioinformatician'
    )

    handler = models.ForeignKey(
        User,
        verbose_name="Handler",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name = 'request_handler'
    )

    pool_size_user = models.ForeignKey(
        PoolSize,
        verbose_name="Sequencing kit (user)",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name = 'request_pool_size_user'
    )

    libraries = models.ManyToManyField(
        Library,
        related_name="request",
        blank=True,
    )

    pooled_libraries = models.BooleanField(
        verbose_name="Pooled libraries?",
        default=False,
    )

    pooled_libraries_concentration_user = models.FloatField(
        "Library pool Concentration by User",
        null=True,
        blank=True,
    )

    pooled_libraries_volume_user = models.FloatField(
        "Library pool Volume by User",
        null=True,
        blank=True,
    )

    pooled_libraries_fragment_size_user = models.PositiveIntegerField(
        "Library pool Mean Fragment Size by User",
        null=True,
        blank=True,
    )

    samples = models.ManyToManyField(
        Sample,
        related_name="request",
        blank=True,
    )

    files = models.ManyToManyField(
        FileRequest,
        related_name="request",
        blank=True,
    )

    deep_seq_request = models.FileField(
        verbose_name="Deep Sequencing Request",
        upload_to="deep_sequencing_requests/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    approval_user = models.ForeignKey(
        User,
        verbose_name="approval user",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name = 'request_approval_user'
    )

    approval_time = models.DateTimeField(verbose_name="Approval Time",
                                             null=True,
                                             default=None,
                                             blank=True,
                                            )

    samples_submitted = models.BooleanField(
        verbose_name="Samples Submitted",
        default=False,
    )

    samples_submitted_time = models.DateTimeField(verbose_name="Samples Submitted Time",
                                                  null=True,
                                                  default=None,
                                                  blank=True,
                                                  )

    sequenced = models.BooleanField(
        verbose_name="Sequenced",
        default=False,
    )

    invoice_date = models.DateTimeField(verbose_name="Invoice Date",
                                    null=True,
                                    default=None,
                                    blank=True,
                                    )

    archived = models.BooleanField("Archived", default=False)

    filepaths = models.JSONField(null=False, default=filepaths_default)

    metapaths = models.JSONField(null=False, default=metapaths_default)

    approval = models.JSONField(null=False, default=approval_default)

    def __str__(self):
        return self.name

    @property
    def records(self):
        return list(itertools.chain(self.samples.all(), self.libraries.all()))

    @property
    def total_sequencing_depth(self):
        return round(sum(x.sequencing_depth for x in self.records), 2)

    @property
    def total_records_count(self):
        return len(self.records)

    @property
    def statuses(self):
        return [x.status for x in self.records]

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        # Do NOT programatically set a request's name, let the user enter it
        # if created:
        #     # Set name after getting an id
        #     self.name = f"{self.id}_{self.user.last_name}"
        #     if self.user.pi:
        #         self.name += "_" + self.user.pi.name
        #     self.save()

    def delete(self, *args, **kwargs):
        # Delete all libraries and samples
        self.libraries.all().delete()
        self.samples.all().delete()

        # Delete all files
        self.files.all().delete()

        super().delete(*args, **kwargs)
