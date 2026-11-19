from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    FixedCosts,
    LibraryPreparationCosts,
    SequencingCosts,
)


@admin.register(FixedCosts)
class FixedCostsAdmin(SimpleHistoryAdmin):
    # Prices are versioned through history records; archiving a price would
    # price old runs as 0, so the flag is not offered here.
    list_display = ("sequencer", "price_amount")


@admin.register(LibraryPreparationCosts)
class LibraryPreparationCostsAdmin(SimpleHistoryAdmin):
    search_fields = (
        "library_protocol__name",
        "price",
    )
    list_display = ("library_protocol", "price_amount")


@admin.register(SequencingCosts)
class SequencingCostsAdmin(SimpleHistoryAdmin):
    search_fields = (
        "sequencer__name",
        "read_length__name",
        "price",
    )
    list_display = ("sequencer", "read_length", "price_amount")
    list_filter = ("sequencer", "read_length")


