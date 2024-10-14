from common.models import DateTimeMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from sample.models import Sample


class LibraryPreparation(DateTimeMixin):
    sample = models.OneToOneField(
        Sample, verbose_name="Sample", on_delete=models.SET_NULL, null=True
    )

    starting_amount = models.FloatField(
        "Starting Amount",
        null=True,
        blank=True,
    )

    spike_in_description = models.TextField(
        "Spike-in Description",
        null=True,
        blank=True,
    )

    spike_in_volume = models.FloatField(
        "Spike-in Volume",
        null=True,
        blank=True,
    )

    pcr_cycles = models.IntegerField(
        "PCR Cycles",
        null=True,
        blank=True,
    )

    concentration_library = models.FloatField(
        "Concentration Library",
        null=True,
        blank=True,
    )

    mean_fragment_size = models.IntegerField(
        "Mean Fragment Size",
        null=True,
        blank=True,
    )

    nM = models.FloatField(
        "nM",
        null=True,
        blank=True,
    )

    removed_qpcr_result = models.FloatField(
        "qPCR Result",
        null=True,
        blank=True,
    )  # This field is not in use

    comments = models.TextField(
        "Comments",
        null=True,
        blank=True,
    )

    smear_analysis = models.FloatField(
        "Smear Analysis",
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Library Preparation"
        verbose_name_plural = "Library Preparation"

    def __str__(self):
        # return '%s (Request: %s)' % (self.sample.name,
        #                              self.sample.request.get())
        return f"{self.sample.name} ({self.sample.barcode})"
