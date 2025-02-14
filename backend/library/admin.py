from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from simple_history.admin import SimpleHistoryAdmin
from .models import Library


@admin.register(Library)
class LibraryAdmin(SimpleHistoryAdmin):
    list_display = (
        "name",
        "barcode",
        "status",
        "request_name",
        "library_protocol",
        "library_type",
        "index_type",
        "index_i7",
        "index_i5",
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
        ("organism", RelatedDropdownFilter),
        ("read_length", RelatedDropdownFilter),
        ("index_type", RelatedDropdownFilter),
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
                ),
            },
        ),
        (
            "Determined by User",
            {
                "fields": (
                    "library_protocol",
                    "library_type",
                    "measuring_unit",
                    "measured_value",
                    "mean_fragment_size",
                    "volume",
                    "read_length",
                    "sequencing_depth",
                    "index_type",
                    "index_reads",
                    "index_i7",
                    "index_i5",
                    "organism",
                    "comments",
                ),
            },
        ),
        (
            "Determined by Facility",
            {
                "fields": (
                    "measuring_unit_facility",
                    "measured_value_facility",
                    "dilution_factor",
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
