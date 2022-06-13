from django.contrib import admin
from .models import LibraryPreparation


@admin.register(LibraryPreparation)
class LibraryPreparationAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'request', 'pool',)
    search_fields = ('sample__name', 'sample__barcode',)
    list_select_related = True

    def name(self, obj):
        return obj.sample.name

    def barcode(self, obj):
        return obj.sample.barcode

    def request(self, obj):
        return obj.sample.request.get().name

    def pool(self, obj):
        return obj.sample.pool.get().name
