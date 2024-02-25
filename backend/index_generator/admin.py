from common.admin import ArchivedFilter
from django.conf import settings
from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from .models import Pool, PoolSize


class BaseInline(admin.TabularInline):
    fields = (
        "name",
        "barcode",
        "status",
        "request",
    )
    readonly_fields = (
        "name",
        "barcode",
        "status",
        "request",
    )
    can_delete = False
    extra = 0

    @admin.display(description="Name")
    def name(self, instance):
        return getattr(instance, self.verbose_name.lower()).name

    @admin.display(description="Barcode")
    def barcode(self, instance):
        return getattr(instance, self.verbose_name.lower()).barcode

    @admin.display(description="Status")
    def status(self, instance):
        return getattr(instance, self.verbose_name.lower()).status

    @admin.display(description="Request")
    def request(self, instance):
        return getattr(instance, self.verbose_name.lower()).request.get().name

    def has_add_permission(self, request, obj=None):
        return False


class LibraryInline(BaseInline):
    model = Pool.libraries.through
    verbose_name = "Library"
    verbose_name_plural = "Libraries"


class SampleInline(BaseInline):
    model = Pool.samples.through
    verbose_name = "Sample"
    verbose_name_plural = "Sample"


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    list_display = ("name", "size", "archived")
    search_fields = (
        "name",
        "size__short_name",
    )
    autocomplete_fields = (
        "user",
    )
    list_filter = ("size", ArchivedFilter)
    inlines = [LibraryInline, SampleInline]
    exclude = (
        "libraries",
        "samples",
    )

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


# Do not show in 'main' admin anymore, now used as inline for
# lane capacity/size of Sequencer
# @admin.register(PoolSize)
class PoolSizeAdmin(admin.ModelAdmin):
    list_display = ("name", "archived")
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
