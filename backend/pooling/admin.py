from common.admin import ArchivedFilter
from django.contrib import admin

from .models import Pooling


@admin.register(Pooling)
class PoolingAdmin(admin.ModelAdmin):
    list_filter = (ArchivedFilter,)
    list_display = ("name", "barcode", "request", "pool", "archived")
    search_fields = (
        "library__name",
        "library__barcode",
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

    # library and sample are on_delete=SET_NULL, so rows can outlive both.

    def name(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.name if instance else ""

    def barcode(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.barcode if instance else ""

    def request(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.request.get().name if instance else ""

    def pool(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.pool.get().name if instance else ""
