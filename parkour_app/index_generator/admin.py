from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from .models import Pool, PoolSize
from django.conf import settings


class BaseInline(admin.TabularInline):
    fields = ('name', 'barcode', 'status', 'request',)
    readonly_fields = ('name', 'barcode', 'status', 'request',)
    can_delete = False
    extra = 0

    def name(self, instance):
        return getattr(instance, self.verbose_name.lower()).name
    name.short_description = 'Name'

    def barcode(self, instance):
        return getattr(instance, self.verbose_name.lower()).barcode
    barcode.short_description = 'Barcode'

    def status(self, instance):
        return getattr(instance, self.verbose_name.lower()).status
    status.short_description = 'Status'

    def request(self, instance):
        return getattr(instance, self.verbose_name.lower()).request.get().name
    request.short_description = 'Request'

    def has_add_permission(self, request):
        return False


class LibraryInline(BaseInline):
    model = Pool.libraries.through
    verbose_name = 'Library'
    verbose_name_plural = 'Libraries'


class SampleInline(BaseInline):
    model = Pool.samples.through
    verbose_name = 'Sample'
    verbose_name_plural = 'Sample'


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'size',)
    search_fields = ('name', 'size__multiplier', 'size__size',)
    list_filter = (('size', RelatedDropdownFilter),)
    inlines = [LibraryInline, SampleInline]
    exclude = ('libraries', 'samples',)


@admin.register(PoolSize)
class PoolSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'obsolete_name')
    actions = ('mark_as_obsolete', 'mark_as_non_obsolete',)

    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    mark_as_obsolete.short_description = "Mark pool size as obsolete"

    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    mark_as_non_obsolete.short_description = "Mark pool size as non-obsolete"

    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"

    obsolete_name.short_description = "STATUS"
