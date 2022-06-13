from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from library_sample_shared.models import GenericLibrarySample


class NucleicAcidType(models.Model):
    name = models.CharField('Name', max_length=100)

    type = models.CharField(
        'Type',
        max_length=3,
        choices=(('DNA', 'DNA'), ('RNA', 'RNA')),
        default='DNA',
    )

    status = models.PositiveIntegerField("Status",default=1)

    class Meta:
        verbose_name = 'Nucleic Acid Type'
        verbose_name_plural = 'Nucleic Acid Types'

    def __str__(self):
        return self.name


class Sample(GenericLibrarySample):
    nucleic_acid_type = models.ForeignKey(
        NucleicAcidType,
        verbose_name='Nucleic Acid Type',
    )

    rna_quality = models.FloatField(
        'RNA Quality',
        validators=[MinValueValidator(0.0), MaxValueValidator(11.0)],
        null=True,
        blank=True,
    )

    is_converted = models.BooleanField('Converted', default=False)

    # Quality Control
    rna_quality_facility = models.FloatField(
        'RNA Quality (facility)',
        validators=[MinValueValidator(0.0), MaxValueValidator(11.0)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Sample'
        verbose_name_plural = 'Samples'

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
