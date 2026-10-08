from django.db import models
from simple_history.models import HistoricalRecords
from flowcell.models import Sequencer
from library_sample_shared.models import LibraryProtocol, ReadLength


class FixedCosts(models.Model):
    history = HistoricalRecords()

    sequencer = models.OneToOneField(Sequencer, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Fixed Cost"
        verbose_name_plural = "Fixed Costs"

    @property
    def price_amount(self):
        return f"{self.price} €"

    def __str__(self):
        return self.sequencer.name if self.sequencer_id else "(deleted)"


class LibraryPreparationCosts(models.Model):
    history = HistoricalRecords()

    library_protocol = models.OneToOneField(
        LibraryProtocol,
        limit_choices_to={"archived": False},
        on_delete=models.SET_NULL,
        null=True,
    )
    # library_protocol = models.OneToOneField(LibraryProtocol)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Library Preparation Cost"
        verbose_name_plural = "Library Preparation Costs"

    @property
    def price_amount(self):
        return f"{self.price} €"

    def __str__(self):
        return self.library_protocol.name if self.library_protocol_id else "(deleted)"


class SequencingCosts(models.Model):
    history = HistoricalRecords()

    sequencer = models.ForeignKey(
        Sequencer,
        limit_choices_to={"archived": False},
        on_delete=models.SET_NULL,
        null=True,
    )
    read_length = models.ForeignKey(
        ReadLength, verbose_name="Read Length", on_delete=models.SET_NULL, null=True
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    archived = models.BooleanField("Archived", default=False)

    class Meta:
        verbose_name = "Sequencing Cost"
        verbose_name_plural = "Sequencing Costs"
        unique_together = (
            "sequencer",
            "read_length",
        )

    @property
    def price_amount(self):
        return f"{self.price} €"

    def __str__(self):
        s = self.sequencer.name if self.sequencer_id else "(deleted)"
        r = self.read_length.name if self.read_length_id else "(deleted)"
        return f"{s} {r}"
