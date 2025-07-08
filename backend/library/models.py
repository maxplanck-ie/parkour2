from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from library_sample_shared.models import GenericLibrarySample
from django.contrib.postgres.fields import ArrayField


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

    percent_total = models.FloatField(
        "Smear Analysis (% Total)",
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
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

class CompleteLibraryData(models.Model):
    library_id = models.IntegerField(primary_key=True)
    barcode = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    status = models.IntegerField()
    sequencing_depth = models.FloatField()
    measuring_unit = models.CharField(max_length=50)
    mean_fragment_size = models.FloatField()
    percent_total = models.FloatField()
    measuring_unit_facility = models.CharField(max_length=100)
    organism_name = models.CharField(max_length=100, null=True)
    library_protocol_name = models.CharField(max_length=150, null=True)
    library_type_name = models.CharField(max_length=200, null=True)
    index_type_name = models.CharField(max_length=100, null=True)
    index_reads = models.PositiveSmallIntegerField(null=True)
    index_i7 = models.CharField(max_length=24, null=True)
    index_i5 = models.CharField(max_length=24, null=True)
    request_id = models.IntegerField()
    request_name = models.CharField(max_length=255)
    pool_name = models.CharField(max_length=100)
    create_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "complete_library_data"
