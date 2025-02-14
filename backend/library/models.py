from django.core.validators import MinValueValidator
from django.db import models
from library_sample_shared.models import GenericLibrarySample


class Library(GenericLibrarySample):
    MEASURING_UNIT_CHOICES = [
        ("Concentration (ng/µl)", "concentration", "Concentration"),
        ("Unknown", "-", "Unknown"),
    ]

    measuring_unit = models.CharField(
        "Measuring Unit",
        max_length=50,
        choices=[
            (unit, display_name)
            for display_name, unit, input_type in MEASURING_UNIT_CHOICES
        ],
        null=True,
        blank=True,
    )

    mean_fragment_size = models.PositiveIntegerField(
        "Mean Fragment Size",
        null=True,
        blank=True,
    )

    removed_qpcr_result = models.FloatField(
        "qPCR Result", null=True, blank=True
    )  # This field is not in use

    removed_qpcr_result_facility = models.FloatField(
        "qPCR Result (facility)",
        null=True,
        blank=True,
    )  # This field is not in use

    archived = models.BooleanField("Archived", default=False)

    measuring_unit_facility = models.CharField(
        "Measuring Unit (facility)",
        max_length=50,
        choices=[
            (unit, display_name)
            for display_name, unit, input_type in MEASURING_UNIT_CHOICES
        ],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Library"
        verbose_name_plural = "Libraries"
