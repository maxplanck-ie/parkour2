from django.contrib import admin

from .models import LibraryPreparation


@admin.register(LibraryPreparation)
class LibraryPreparationAdmin(admin.ModelAdmin):
    list_display = ("name", "barcode", "request", "pool", "archived")
    list_filter = ("archived",)
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

    def name(self, obj):
        return obj.sample.name

    def barcode(self, obj):
        return obj.sample.barcode

    def request(self, obj):
        return obj.sample.request.get().name

    def pool(self, obj):
        return obj.sample.pool.get().name
