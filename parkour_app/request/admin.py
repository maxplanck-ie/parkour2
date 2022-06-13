from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from request.models import Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'request_uploaded', 'samples_submitted',
                    'sequenced',)
    list_select_related = True

    search_fields = ('name', 'user__first_name', 'user__last_name',
                     'user__email')

    filter_horizontal = ('libraries', 'samples', 'files',)

    list_filter = (('user', RelatedDropdownFilter), 'sequenced',)

    def request_uploaded(self, obj):
        return obj.deep_seq_request.name != ''
    request_uploaded.boolean = True
