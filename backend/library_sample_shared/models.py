from common.models import DateTimeMixin
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

AlphaValidator = RegexValidator(
    r"^[A-Z]$", "Only capital alphabetical characters are allowed."
)


class Organism(models.Model):
    name = models.CharField("Name", max_length=100)
    label = models.CharField("Label", max_length=25, null=True, blank=True)
    yaml = models.CharField("YAML", max_length=200, null=True, blank=True)
    scientific_name = models.CharField(
        "Scientific Name",
        max_length=150,
        blank=True,
        null=True,
    )
    taxon_id = models.PositiveIntegerField(
        "Taxon Identifier",
        blank=True,
        null=True,
    )
    archived = models.BooleanField("Archived", default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ConcentrationMethod(models.Model):
    name = models.CharField("Name", max_length=100)

    class Meta:
        verbose_name = "Concentration Method"
        verbose_name_plural = "Concentration Methods"

    def __str__(self):
        return self.name


class ReadLength(models.Model):
    name = models.CharField("Name", max_length=50)
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Read Length"
        verbose_name_plural = "Read Lengths"

    def __str__(self):
        return self.name


class GenericIndex(models.Model):
    prefix = models.CharField("Prefix", max_length=20, default="")
    number = models.CharField("Number", max_length=15, default="")
    index = models.CharField("Index", max_length=24)

    @property
    def index_id(self):
        return f"{self.prefix}{self.number}"

    class Meta:
        abstract = True
        unique_together = (
            "prefix",
            "number",
        )

    def __str__(self):
        return self.index_id

    def type(self):
        try:
            index_type = self.index_type.get()
        except AttributeError:
            return ""
        else:
            return index_type.name


class IndexI7(GenericIndex):
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Index I7"
        verbose_name_plural = "Indices I7"


class IndexI5(GenericIndex):
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Index I5"
        verbose_name_plural = "Indices I5"


class IndexType(models.Model):
    name = models.CharField("Name", max_length=100)
    is_dual = models.BooleanField("Is Dual", default=False)

    index_length = models.CharField(
        "Index Length",
        max_length=2,
        choices=(("6", "6"), ("8", "8"), ("10", "10"), ("12", "12"), ("24", "24")),
        default="8",
    )

    format = models.CharField(
        "Format",
        max_length=11,
        choices=(
            ("single", "single tube"),
            ("plate", "plate"),
        ),
        default="single",
    )

    indices_i7 = models.ManyToManyField(
        IndexI7,
        verbose_name="Indices I7",
        related_name="index_type",
        blank=True,
    )

    indices_i5 = models.ManyToManyField(
        IndexI5,
        verbose_name="Indices I5",
        related_name="index_type",
        blank=True,
    )

    read_type = models.CharField(
        "Read Type",
        max_length=11,
        choices=(
            ("short", "short read"),
            ("long", "long read"),
        ),
        default="short",
    )

    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Index Type"
        verbose_name_plural = "Index Types"

    def __str__(self):
        return self.name


class IndexPair(models.Model):
    index_type = models.ForeignKey(
        IndexType, verbose_name="Index Type", on_delete=models.SET_NULL, null=True
    )
    index1 = models.ForeignKey(
        IndexI7,
        verbose_name="Index 1",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    index2 = models.ForeignKey(
        IndexI5,
        verbose_name="Index 2",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    char_coord = models.CharField(
        "Character Coordinate", validators=[AlphaValidator], max_length=1
    )

    num_coord = models.PositiveSmallIntegerField(
        "Numeric Coordinate", validators=[MinValueValidator(1)]
    )

    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Index Pair"
        verbose_name_plural = "Index Pairs"

    @property
    def coordinate(self):
        return f"{self.char_coord}{self.num_coord}"

    def __str__(self):
        index1_id = self.index1.index_id if self.index1 else ""
        index2_id = self.index2.index_id if self.index2 else ""
        output = index1_id
        if self.index_type.is_dual:
            output += f"-{index2_id}"
        return output


class BarcodeCounter(models.Model):
    year = models.PositiveSmallIntegerField(default=2018, unique=True)

    last_id = models.PositiveSmallIntegerField(default=0)

    @classmethod
    def load(cls, year=timezone.now().year):
        obj, created = cls.objects.get_or_create(year=year)
        return obj

    def increment(self):
        self.last_id += 1

    def __str__(self):
        return str(self.last_id)


class LibraryProtocol(models.Model):
    name = models.CharField("Name", max_length=150)
    type = models.CharField(
        "Type",
        max_length=5,
        choices=(("DNA", "DNA"), ("RNA", "RNA"), ("Cells", "Cells")),
        default="DNA",
    )
    provider = models.CharField("Provider", max_length=150)
    catalog = models.CharField("Catalog", max_length=150)
    explanation = models.CharField("Explanation", max_length=250)
    input_requirements = models.CharField("Input Requirements", max_length=150)
    typical_application = models.CharField(
        "Typical Application",
        max_length=200,
    )

    status = models.PositiveIntegerField("Status", default=1)
    comments = models.TextField("Comments", null=True, blank=True)
    archived = models.BooleanField("Archived", default=False)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Library Protocol"
        verbose_name_plural = "Library Protocols"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created:
            # When a new library protocol is created, add it to the list of
            # protocols of the Library Type 'Other'. If the latter does not
            # exist, create it
            try:
                library_type = LibraryType.objects.filter(archived=False).get(
                    name="Other"
                )
            except LibraryType.DoesNotExist:
                library_type = LibraryType(name="Other")
                library_type.save()
            finally:
                if self.name != "Quality Control":
                    library_type.library_protocol.add(self)


class LibraryType(models.Model):
    name = models.CharField("Name", max_length=200)
    library_protocol = models.ManyToManyField(
        LibraryProtocol,
        verbose_name="Library Protocol",
    )
    archived = models.BooleanField("Archived", default=False)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Library Type"
        verbose_name_plural = "Library Types"

    def __str__(self):
        return self.name


def get_removed_concentrationmethod():
    return ConcentrationMethod.objects.get_or_create(
        name="Removed Concentration Method"
    )[0]


class GenericLibrarySample(DateTimeMixin):
    name = models.CharField(
        "Name",
        max_length=200,
    )

    status = models.SmallIntegerField(default=0)

    library_protocol = models.ForeignKey(
        LibraryProtocol,
        verbose_name="Library Protocol",
        on_delete=models.SET_NULL,
        null=True,
    )

    library_type = models.ForeignKey(
        LibraryType,
        verbose_name="Library Type",
        on_delete=models.SET_NULL,
        null=True,
    )

    organism = models.ForeignKey(
        Organism, verbose_name="Organism", on_delete=models.SET_NULL, null=True
    )

    measured_value = models.FloatField(
        "Measured Value", validators=[MinValueValidator(-1)], null=True, blank=True
    )

    removed_concentration_method = models.ForeignKey(
        ConcentrationMethod,
        verbose_name="Concentration Method",
        null=True,
        blank=True,
        on_delete=models.SET(get_removed_concentrationmethod),
    )  # This field is not in use

    removed_equal_representation_nucleotides = models.BooleanField(
        "Equal Representation of Nucleotides",
        blank=True,
        default=False,
    )  # This field is not in use

    volume = models.FloatField(
        "Volume", validators=[MinValueValidator(10)], null=True, blank=True
    )

    read_length = models.ForeignKey(
        ReadLength,
        verbose_name="Read Length",
        on_delete=models.SET_NULL,
        null=True,
    )

    sequencing_depth = models.FloatField("Sequencing Depth")

    comments = models.TextField("Comments", null=True, blank=True)

    is_pooled = models.BooleanField("Pooled", default=False)

    barcode = models.CharField("Barcode", max_length=9)

    index_type = models.ForeignKey(
        IndexType,
        verbose_name="Index Type",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    index_reads = models.PositiveSmallIntegerField("Index Reads", default=0)

    index_i7 = models.CharField(
        "Index I7",
        max_length=24,
        null=True,
        blank=True,
    )

    index_i5 = models.CharField(
        "Index I5",
        max_length=24,
        null=True,
        blank=True,
    )

    removed_amplification_cycles = models.PositiveIntegerField(
        "Amplification cycles",
        null=True,
        blank=True,
    )  # This field is not in use

    @property
    def index_i7_id(self):
        indices = self.index_type.indices_i7.all() if self.index_type else []
        index_id = [x.index_id for x in indices if x.index == self.index_i7]
        return index_id[0] if any(index_id) else ""

    @property
    def index_i5_id(self):
        indices = self.index_type.indices_i5.all() if self.index_type else []
        index_id = [x.index_id for x in indices if x.index == self.index_i5]
        return index_id[0] if any(index_id) else ""

    # Facility

    dilution_factor = models.PositiveIntegerField(
        "Dilution Factor",
        default=1,
        blank=True,
    )

    removed_concentration_method_facility = models.ForeignKey(
        ConcentrationMethod,
        related_name="+",
        verbose_name="Concentration Method",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )  # This field is not in use

    sample_volume_facility = models.PositiveIntegerField(
        "Sample Volume",
        null=True,
        blank=True,
    )

    amount_facility = models.FloatField(
        "Amount",
        null=True,
        blank=True,
    )

    size_distribution_facility = models.FloatField(
        "Size Distribution",
        null=True,
        blank=True,
    )

    comments_facility = models.TextField(
        "Comments",
        null=True,
        blank=True,
    )

    measured_value_facility = models.FloatField(
        "Measured Value (facility)",
        validators=[MinValueValidator(-1)],
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def generate_barcode(self):
        counter = BarcodeCounter.load()
        counter.increment()
        counter.save()

        record_type = self.__class__.__name__[0]
        barcode = timezone.now().strftime("%y") + record_type
        barcode += "0" * (6 - len(str(counter))) + str(counter)

        self.barcode = barcode
        self.save(update_fields=["barcode"])

    def get_measuring_unit_details(self):
        for display_name, unit, input_type in self.MEASURING_UNIT_CHOICES:
            if display_name == self.measuring_unit:
                return display_name, unit, input_type
        return None, None, None

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        if created:
            self.generate_barcode()

    def __str__(self):
        return self.name
