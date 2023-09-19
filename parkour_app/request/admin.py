from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from request.models import Request
from common.admin import ArchivedFilter


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "request_uploaded",
        "samples_submitted",
        "sequenced",
        "archived",
    )
    list_select_related = True

    search_fields = ("name", "user__first_name", "user__last_name", "user__email")

    filter_horizontal = (
        "libraries",
        "samples",
        "files",
    )

    list_filter = (("user", RelatedDropdownFilter), "sequenced", ArchivedFilter)

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

    @admin.display(boolean=True)
    def request_uploaded(self, obj):
        return obj.deep_seq_request.name != ""
