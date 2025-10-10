from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from library_sample_shared.models import GenericLibrarySample
from django.contrib.postgres.fields import ArrayField


class NucleicAcidType(models.Model):
    name = models.CharField("Name", max_length=100)

    type = models.CharField(
        "Type",
        max_length=5,
        choices=(("DNA", "DNA"), ("RNA", "RNA"), ("Cells", "Cells")),
        default="DNA",
    )

    status = models.PositiveIntegerField("Status", default=1)

    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Input Type"
        verbose_name_plural = "Input Types"

    def __str__(self):
        return self.name


class Sample(GenericLibrarySample):
    MEASURING_UNIT_CHOICES = [
        ("ng/µl (Concentration)", "ng/µl", "Concentration"),
        ("M (Cells)", "M", "Cells"),
        ("k (Cells)", "k", "Cells"),
        ("Unknown", "Unknown", "Unknown"),
    ]

    BIOSAFETY_LEVEL_CHOICES = [("BSL1", "bsl1"), ("BSL2", "bsl2")]

    nucleic_acid_type = models.ForeignKey(
        NucleicAcidType,
        verbose_name="Input Type",
        on_delete=models.SET_NULL,
        null=True,
    )

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

    rna_quality = models.FloatField(
        "RNA Quality",
        validators=[MinValueValidator(0.0), MaxValueValidator(11.0)],
        null=True,
        blank=True,
    )

    is_converted = models.BooleanField("Converted", default=False)

    rna_quality_facility = models.FloatField(
        "RNA Quality (facility)",
        validators=[MinValueValidator(0.0), MaxValueValidator(11.0)],
        null=True,
        blank=True,
    )

    biosafety_level = models.CharField(
        "Biosafety Level",
        max_length=50,
        choices=[
            (biosafety_level, display_name)
            for display_name, biosafety_level in BIOSAFETY_LEVEL_CHOICES
        ],
        null=True,
    )

    gmo = models.BooleanField("Genetically Modified Organism", null=True, blank=True)

    # Facility

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

    gmo_facility = models.BooleanField(
        "Genetically Modified Organism (facility)", null=True, blank=True
    )

    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Sample"
        verbose_name_plural = "Samples"

    # def save(self, *args, **kwargs):
    #     # prev_obj = type(self).objects.get(pk=self.pk) if self.pk else None
    #     created = self.pk is None
    #     super().save(*args, **kwargs)

    #     if created:
    #         # Create barcode
    #         counter = BarcodeCounter.load()
    #         counter.increment()
    #         counter.save()

    #         self.barcode = generate_barcode('S', str(counter.counter))
    #         self.save(update_fields=['barcode'])

    #     # When a Library Preparation object passes the quality check and
    #     # the corresponding sample's status changes to 3,
    #     # create a Pooling object
    #     # if prev_obj and prev_obj.status in [2, -2] and self.status == 3:
    #     #     pooling_obj = Pooling(sample=self)
    #     #     pooling_obj.save()


class CompleteSampleData(models.Model):
    sample_id = models.IntegerField(primary_key=True)
    barcode = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    status = models.IntegerField()
    sequencing_depth = models.FloatField()
    nucleic_acid_type_id = models.IntegerField()
    nucleic_acid_type_name = models.CharField(max_length=100)
    measuring_unit = models.CharField(max_length=50)
    measured_value = models.FloatField()
    concentration_library = models.FloatField()
    gmo = models.BooleanField()
    library_protocol_id = models.IntegerField()
    library_protocol_name = models.CharField(max_length=150, null=True)
    analysis_type_id = models.IntegerField()
    analysis_type_name = models.CharField(max_length=200, null=True)
    read_length_id = models.IntegerField(null=True)
    read_length_name = models.CharField(max_length=50, null=True)
    average_fragment_size = models.FloatField()
    starting_amount = models.FloatField()
    pcr_cycles = models.IntegerField()
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
        db_table = "complete_sample_data_mv"
