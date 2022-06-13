from django.contrib import admin
from .models import Pooling


@admin.register(Pooling)
class PoolingAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'request', 'pool',)
    search_fields = ('library__name', 'library__barcode', 'sample__name',
                     'sample__barcode',)
    list_select_related = True

    def name(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.name

    def barcode(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.barcode

    def request(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.request.get().name

    def pool(self, obj):
        instance = obj.library if obj.library else obj.sample
        return instance.pool.get().name
