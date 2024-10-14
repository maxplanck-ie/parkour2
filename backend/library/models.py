from django.core.validators import MinValueValidator
from django.db import models
from library_sample_shared.models import GenericLibrarySample


class Library(GenericLibrarySample):
    MEASURING_UNIT_CHOICES = [
        ("bp (DNA)", "bp", "DNA"),
        ("Measure for Me", "-", "Measure"),
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

    measured_value = models.FloatField(
        "Measured Value", validators=[MinValueValidator(-1)], null=True, blank=True
    )

    archived = models.BooleanField("Archived", default=False)

    removed_qpcr_result = models.FloatField(
        "qPCR Result", null=True, blank=True
    )  # This field is not in use

    removed_qpcr_result_facility = models.FloatField(
        "qPCR Result (facility)",
        null=True,
        blank=True,
    )  # This field is not in use

    class Meta:
        verbose_name = "Library"
        verbose_name_plural = "Libraries"
