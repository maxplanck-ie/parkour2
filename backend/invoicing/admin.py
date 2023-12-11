from common.admin import ArchivedFilter
from django.contrib import admin

from .models import (
    FixedCosts,
    InvoicingReport,
    LibraryPreparationCosts,
    SequencingCosts,
)


@admin.register(InvoicingReport)
class InvoicingReportAdmin(admin.ModelAdmin):
    pass


@admin.register(FixedCosts)
class FixedCostsAdmin(admin.ModelAdmin):
    list_display = ("sequencer", "price_amount", "archived")

    list_filter = (ArchivedFilter,)

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)


@admin.register(LibraryPreparationCosts)
class LibraryPreparationCostsAdmin(admin.ModelAdmin):
    search_fields = (
        "library_protocol__name",
        "price",
    )
    list_display = ("library_protocol", "price_amount", "archived")

    list_filter = (ArchivedFilter,)

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)


@admin.register(SequencingCosts)
class SequencingCostsAdmin(admin.ModelAdmin):
    search_fields = (
        "sequencer__name",
        "read_length__name",
        "price",
    )
    list_display = ("sequencer", "read_length", "price_amount", "archived")
    list_filter = ("sequencer", "read_length", ArchivedFilter)

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)
