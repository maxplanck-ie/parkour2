from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    FixedCosts,
    InvoicingReport,
    LibraryPreparationCosts,
    SequencingCosts,
    FixedPrice,
    SequencingPrice,
    LibraryPreparationPrice
)


class FixedPriceInline(admin.TabularInline):
    model = FixedPrice
    fields = ('price', 'organization',)
    extra = 1


class SequencingPriceInline(admin.TabularInline):
    model = SequencingPrice
    fields = ('price', 'organization',)
    extra = 1


class LibraryPreparationPriceInline(admin.TabularInline):
    model = LibraryPreparationPrice
    fields = ('price', 'organization',)
    extra = 1


@admin.register(InvoicingReport)
class InvoicingReportAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "organization",
        "download_report_link",
    )

    list_filter = (
        "organization",
        "month"
    )

    def download_report_link(self, obj):
        return mark_safe(f'<a href={obj.report.url}>Download</a>') if obj.report else None
    download_report_link.short_description = 'Report'

@admin.register(FixedCosts)
class FixedCostsAdmin(admin.ModelAdmin):
    inlines = [FixedPriceInline]
    list_display = (
        "sequencer",
        "price_amounts",
    )

    def price_amounts(self, obj):
        try:
            return ', '.join([f"{o}: {p} €" for o, p in obj.fixedprice_set.all().values_list('organization__name', 'price')])
        except:
            return ''


@admin.register(LibraryPreparationCosts)
class LibraryPreparationCostsAdmin(admin.ModelAdmin):
    inlines = [LibraryPreparationPriceInline]
    search_fields = (
        "library_protocol__name",
        "price",
    )
    list_display = (
        "library_protocol",
        "price_amounts",
    )

    def price_amounts(self, obj):
        try:
            return ', '.join([f"{o}: {p} €" for o, p in obj.librarypreparationprice_set.all().values_list('organization__name', 'price')])
        except:
            return ''


@admin.register(SequencingCosts)
class SequencingCostsAdmin(admin.ModelAdmin):
    inlines = [SequencingPriceInline]
    search_fields = (
        "sequencer__name",
        "read_length__name",
        "price",
    )
    list_display = (
        "sequencer",
        "read_length",
        "price_amounts",
    )
    list_filter = (
        "sequencer",
        "read_length",
    )

    def price_amounts(self, obj):
        try:
            return ', '.join([f"{o}: {p} €" for o, p in obj.sequencingprice_set.all().values_list('organization__name', 'price')])
        except:
            return ''