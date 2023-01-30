import calendar

from common.models import DateTimeMixin, OrganizationMixin
from django.db import models
from flowcell.models import Sequencer
from library_sample_shared.models import LibraryProtocol, ReadLength
from month.models import MonthField


class InvoicingReport(DateTimeMixin, OrganizationMixin):
    month = MonthField("Month")
    report = models.FileField(
        verbose_name="Report",
        upload_to="invoicing/%Y/%m/",
    )

    class Meta:
        verbose_name = "Invoicing Report"
        verbose_name_plural = "Invoicing Report"
        ordering = ["-month"]
        constraints = [
            models.UniqueConstraint(fields=['month', 'organization'],
                                    name='unique_month_organization')
        ]

    def __str__(self):
        return f"{calendar.month_name[self.month.month]} {self.month.year}"


class FixedPrice(OrganizationMixin):

    price = models.DecimalField(max_digits=8, decimal_places=2)

    fixed_cost = models.ForeignKey(
        'FixedCosts',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fixed_cost', 'organization'],
                                    name='unique_fixed_cost_organization')
        ]

    @property
    def price_amount(self):
        return f"{self.price} €"

    def __str__(self):
        return f'{self.fixed_cost} - {self.organization}'


class FixedCosts(models.Model):
    sequencer = models.OneToOneField(Sequencer, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Fixed Cost"
        verbose_name_plural = "Fixed Costs"

    def __str__(self):
        return self.sequencer.name


class LibraryPreparationPrice(OrganizationMixin):
    
    price = models.DecimalField(max_digits=8, decimal_places=2)

    library_preparation_cost = models.ForeignKey(
        'LibraryPreparationCosts',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['library_preparation_cost', 'organization'],
                                    name='unique_library_preparation_cost_organization')
        ]

    @property
    def price_amount(self):
        return f"{self.price} €"
    
    def __str__(self):
        return f'{self.library_preparation_cost} - {self.organization}'


class LibraryPreparationCosts(models.Model):
    library_protocol = models.OneToOneField(
        LibraryProtocol,
        limit_choices_to={"obsolete": 1},
        on_delete=models.SET_NULL,
        null=True,
    )
    # library_protocol = models.OneToOneField(LibraryProtocol)

    class Meta:
        verbose_name = "Library Preparation Cost"
        verbose_name_plural = "Library Preparation Costs"

    def __str__(self):
        return self.library_protocol.name


class SequencingPrice(OrganizationMixin):

    price = models.DecimalField(max_digits=8, decimal_places=2)

    sequencing_cost = models.ForeignKey(
        'SequencingCosts',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sequencing_cost', 'organization'],
                                    name='unique_sequencing_cost_organization')
        ]

    @property
    def price_amount(self):
        return f"{self.price} €"

    def __str__(self):
        return f'{self.sequencing_cost} - {self.organization}'

class SequencingCosts(models.Model):
    sequencer = models.ForeignKey(
        Sequencer,
        limit_choices_to={"obsolete": 1},
        on_delete=models.SET_NULL,
        null=True,
    )
    read_length = models.ForeignKey(
        ReadLength, verbose_name="Read Length", on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = "Sequencing Cost"
        verbose_name_plural = "Sequencing Costs"
        unique_together = (
            "sequencer",
            "read_length",
        )

    def __str__(self):
        return f"{self.sequencer.name} {self.read_length.name}"
