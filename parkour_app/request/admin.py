from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from request.models import Request, FileRequest


@admin.register(FileRequest)
class FileRequestAdmin(admin.ModelAdmin):
    search_fields = ('name', )


    def has_module_permission(self, request):
        return False

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "request_uploaded",
        "samples_submitted",
        "sequenced",
    )
    list_select_related = True

    search_fields = ("name", "user__first_name", "user__last_name", "user__email")

    autocomplete_fields = (
        "libraries",
        "samples",
        "files",
        "user",
        "pi",
    )

    list_filter = (
        ("user", RelatedDropdownFilter),
        "sequenced",
    )

    def request_uploaded(self, obj):
        return obj.deep_seq_request.name != ""

    request_uploaded.boolean = True

    def get_search_results(self, request, queryset, search_term):

        if request.GET.get('field_name', '') == 'pi':
            queryset, use_distinct = super(RequestAdmin, self).get_search_results(request, queryset, search_term)
            return queryset.filter(is_pi=True), use_distinct
