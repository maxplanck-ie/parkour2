from typing import Any
from common.admin import ArchivedFilter
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
        'id',
        "name",
        "user",
        "request_uploaded",
        "samples_submitted",
        "sequenced",
        "archived",
    )
    list_select_related = True

    search_fields = ("name", "user__first_name", "user__last_name", "user__email")

    autocomplete_fields = (
        "libraries",
        "samples",
        "files",
        "user",
        "pi",
        "bioinformatician",
    )

    list_filter = (
        ("user", RelatedDropdownFilter),
        ("pi", RelatedDropdownFilterPi),
        "sequenced",)

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    readonly_fields = ('token', 'approval_user',
                       'approval_time', 'approval',)

    def save_model(self, request, obj, form, change):

        # Set explicit PK when creating a new Request, do not rely on the
        # DB autoincrement value because it does not know what the last
        # actual Request ID in the DB is
        # NZ, disable/amend this if you need to use an ID other than the
        # next integer after the largest Request ID in the DB
        if obj.pk == None and Request.objects.exists():
            obj.id = Request.objects.order_by('-id').first().id + 1

        return super().save_model(request, obj, form, change)


    def change_view(self, request, object_id, form_url="", extra_context=None):

        if request.user.is_superuser:
            self.readonly_fields = ()

        return super().change_view(request, object_id, form_url, extra_context)

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        queryset.update(archived=True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)

    @admin.display(boolean=True)
    def request_uploaded(self, obj):
        return obj.deep_seq_request.name != ""

    def get_search_results(self, request, queryset, search_term):

        queryset, use_distinct = super(RequestAdmin, self).get_search_results(request, queryset, search_term)
        if request.GET.get('field_name', '') == 'pi':
            return queryset.filter(is_pi=True), use_distinct
        
        return queryset, use_distinct