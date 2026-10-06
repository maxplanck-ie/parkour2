from common.admin import ArchivedFilter
from django.contrib import admin

from .models import LibraryPreparation


@admin.register(LibraryPreparation)
class LibraryPreparationAdmin(admin.ModelAdmin):
    list_display = ("name", "barcode", "request", "pool", "smear_analysis", "archived")
    list_filter = (ArchivedFilter,)
    search_fields = (
        "sample__name",
        "sample__barcode",
    )
    list_select_related = True

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

    # sample is on_delete=SET_NULL, so rows can outlive their sample.

    def name(self, obj):
        return obj.sample.name if obj.sample else ""

    def barcode(self, obj):
        return obj.sample.barcode if obj.sample else ""

    def request(self, obj):
        return obj.sample.request.get().name if obj.sample else ""

    def pool(self, obj):
        return obj.sample.pool.get().name if obj.sample else ""
