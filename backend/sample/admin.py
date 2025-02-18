from common.admin import ArchivedFilter
from django.conf import settings
from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from simple_history.admin import SimpleHistoryAdmin

from .models import NucleicAcidType, Sample


@admin.register(NucleicAcidType)
class NucleicAcidTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "archived")

    list_filter = ("type", ArchivedFilter)

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


@admin.register(Sample)
class SampleAdmin(SimpleHistoryAdmin):
    list_display = (
        "name",
        "barcode",
        "status",
        "request_name",
        "library_protocol",
        "library_type",
        "archived",
    )

    list_select_related = True

    readonly_fields = (
        "create_time",
        "update_time",
    )

    search_fields = (
        "name",
        "barcode",
        "library_protocol__name",
        "library_type__name",
        "request__name",
    )

    list_filter = (
        ("library_protocol", RelatedDropdownFilter),
        ("library_type", RelatedDropdownFilter),
        ("nucleic_acid_type", RelatedDropdownFilter),
        ("organism", RelatedDropdownFilter),
        ("read_length", RelatedDropdownFilter),
        ("index_type", RelatedDropdownFilter),
        ArchivedFilter,
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "status",
                    "barcode",
                    "is_pooled",
                    "is_converted",
                ),
            },
        ),
        (
            "Determined by User",
            {
                "fields": (
                    "library_protocol",
                    "library_type",
                    "nucleic_acid_type",
                    "measuring_unit",
                    "measured_value",
                    "volume",
                    "read_length",
                    "sequencing_depth",
                    "index_type",
                    "index_i7",
                    "index_i5",
                    "organism",
                    "biosafety_level",
                    "gmo",
                ),
            },
        ),
        (
            "Determined by Facility",
            {
                "fields": (
                    "measuring_unit_facility",
                    "measured_value_facility",
                    "gmo_facilitydilution_factor",
                    "sample_volume_facility",
                    "amount_facility",
                    "size_distribution_facility",
                    "comments_facility",
                ),
            },
        ),
        (
            "Other",
            {
                "fields": (
                    "create_time",
                    "update_time",
                ),
            },
        ),
    )

    def request_name(self, obj):
        request = obj.request.filter()
        return request[0].name if request else None

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
