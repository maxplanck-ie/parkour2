from django.contrib import admin

from .models import (
    InvoicingReport,
    FixedCosts,
    LibraryPreparationCosts,
    SequencingCosts,
)


@admin.register(InvoicingReport)
class InvoicingReportAdmin(admin.ModelAdmin):
    pass


@admin.register(FixedCosts)
class FixedCostsAdmin(admin.ModelAdmin):
    list_display = ('sequencer', 'price_amount',)


@admin.register(LibraryPreparationCosts)
class LibraryPreparationCostsAdmin(admin.ModelAdmin):
    search_fields = ('library_protocol__name', 'price',)
    list_display = ('library_protocol', 'price_amount',)


@admin.register(SequencingCosts)
class SequencingCostsAdmin(admin.ModelAdmin):
    search_fields = ('sequencer__name', 'read_length__name', 'price',)
    list_display = ('sequencer', 'read_length', 'price_amount',)
    list_filter = ('sequencer', 'read_length',)
