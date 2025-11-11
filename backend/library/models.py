from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from library_sample_shared.models import GenericLibrarySample
from django.contrib.postgres.fields import ArrayField


class Library(GenericLibrarySample):
    MEASURING_UNIT_CHOICES = [
        ("ng/µl (Concentration)", "ng/µl", "Concentration"),
        ("Unknown", "Unknown", "Unknown"),
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
    measured_value = models.FloatField()
    concentration_library = models.FloatField()
    percent_total = models.FloatField()
    library_protocol_id = models.IntegerField()
    library_protocol_name = models.CharField(max_length=150, null=True)
    analysis_type_id = models.IntegerField()
    analysis_type_name = models.CharField(max_length=200, null=True)
    read_length_id = models.IntegerField(null=True)
    read_length_name = models.CharField(max_length=50, null=True)
    average_fragment_size = models.FloatField()
    index_type_name = models.CharField(max_length=100, null=True)
    coordinate = models.CharField(max_length=3, null=True)
    index_i7 = models.CharField(max_length=24, null=True)
    i7_id = models.CharField(max_length=50, null=True)
    index_i5 = models.CharField(max_length=24, null=True)
    i5_id = models.CharField(max_length=50, null=True)
    request_id = models.IntegerField()
    request_name = models.CharField(max_length=255)
    create_time = models.DateTimeField()
    pool_names = ArrayField(models.CharField(max_length=100), null=True)
    flowcell_ids = ArrayField(models.CharField(max_length=50), null=True)
    sequencer_ids = ArrayField(models.IntegerField(), null=True)
    sequencer_names = ArrayField(models.CharField(max_length=50), null=True)

    class Meta:
        managed = False
        db_table = "complete_library_data_mv"
