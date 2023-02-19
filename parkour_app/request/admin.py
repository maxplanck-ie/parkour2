from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from request.models import Request, FileRequest


class RelatedDropdownFilterPi(RelatedDropdownFilter):

    def field_choices(self, field, request, model_admin):
        pk_qs =  model_admin.get_queryset(request).filter(pi__is_pi=True).distinct().values_list('%s__pk' % self.field_path, flat=True)
        ordering = self.field_admin_ordering(field, request, model_admin)
        return field.get_choices(include_blank=False, limit_choices_to={'pk__in': pk_qs}, ordering=ordering)

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
        ("pi", RelatedDropdownFilterPi),
        "sequenced",
    )

    @admin.display(boolean=True)
    def request_uploaded(self, obj):
        return obj.deep_seq_request.name != ""


    def get_search_results(self, request, queryset, search_term):

        queryset, use_distinct = super(RequestAdmin, self).get_search_results(request, queryset, search_term)
        if request.GET.get('field_name', '') == 'pi':
            return queryset.filter(is_pi=True), use_distinct
        
        return queryset, use_distinct