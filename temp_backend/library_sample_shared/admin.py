import re
from dataclasses import dataclass
from zipfile import BadZipFile

from common.admin import ArchivedFilter
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, resolve
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from openpyxl import load_workbook
from zipfile import BadZipFile 
from dataclasses import dataclass
import re
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render

from .forms import IndexTypeForm
from .models import (
    ConcentrationMethod,
    IndexI5,
    IndexI7,
    IndexPair,
    IndexType,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)


@admin.register(Organism)
class OrganismAdmin(admin.ModelAdmin):
    list_display = ("name", "scientific_name", "taxon_id", "archived")

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


@admin.register(ConcentrationMethod)
class ConcentrationMethodAdmin(admin.ModelAdmin):
    pass


@admin.register(ReadLength)
class ReadLengthAdmin(admin.ModelAdmin):
    list_display = ("name", "archived")
    search_fields = ('name',)
    ordering = ('name',)

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


class IndexI7Inline(admin.TabularInline):
    model = IndexI7
    extra = 2


class IndexPairInline(admin.TabularInline):
    model = IndexPair
    extra = 2

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kw_args = resolve(request.path_info).kwargs
        index_type_id = kw_args.get('object_id', None)

        if db_field.name == "index1":
            kwargs["queryset"] = IndexI7.objects.filter(
                archived=False, index_type__id=index_type_id
            )

        elif db_field.name == "index2":
            kwargs["queryset"] = IndexI5.objects.filter(
                archived=False, index_type__id=index_type_id
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(IndexType)
class IndexTypeAdmin(ImportExportModelAdmin):
    form = IndexTypeForm

    list_display = ("name", "index_length", "is_dual", "format", "archived")

    list_filter = (ArchivedFilter,)

    filter_horizontal = (
        "indices_i7",
        "indices_i5",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "read_type",
                    "index_length",
                    "format",
                    "is_dual",
                    "indices_i7",
                    "indices_i5",
                ),
            },
        ),
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

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Display inline when the object has been saved and
        # the format has been set to 'plate'
        self.inlines = []
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            pass
        else:
            if obj.format == "plate":
                self.inlines = [IndexPairInline]
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(IndexPair)
class IndexPairAdmin(admin.ModelAdmin):
    list_display = ("index_pair", "coordinate", "archived")
    search_fields = ("index_type__name",)
    autocomplete_fields = (
        "index1",
        "index2",
    )
    list_filter = ("index_type", ArchivedFilter)

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

    def index_pair(self, obj):
        return str(obj)

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields[
            "index_type"
        ].queryset = IndexType.objects.filter(archived=False, format="plate")
        return super().render_change_form(request, context, args, kwargs)

    def get_urls(self):
        return [
            path("import_index_pairs/",
                self.admin_site.admin_view(self.import_index_pairs)),
            *super().get_urls(),
        ]

    def import_index_pairs(self, request):

        error = ''
        
        # Import Index Pairs from an Excel spreadsheet

        # If the form has been posted
        if request.method == 'POST':

            try:

                if not "file" in request.FILES:
                    raise Exception("You did not select any file to import.")

                @dataclass
                class IndexPairForImport:
                    index1_prefix: str
                    index1_name: str
                    index1_sequence: str
                    index2_prefix: str
                    index2_name: str
                    index2_sequence: str
                    coordinate: str
                    index_type: str

                # Load workbook
                wb = load_workbook(filename=request.FILES['file'].file)

                # Check that file contains only one worksheet
                if len(wb.worksheets) > 1:
                    raise Exception("The file could not be imported because it contains more than one sheet.")

                # Load firt sheet
                sheet = wb.worksheets[0]

                # Get rows
                rows = iter(sheet)

                # Get table header
                header = next(rows)
                header_values = [str(cell.value).strip().lower() for cell in header if cell.value]

                # Check that column headers are named and ordered as expected
                expected_header_values = ["index1_prefix", "index1_name", "index1_sequence", "index2_prefix",
                                        "index2_name", "index2_sequence", "coordinate", "index_type"]
                if header_values != expected_header_values:
                    raise Exception("The file could not be imported because the column titles do not "
                                    "match the expected values: index1_prefix, index1_name, index1_sequence, "
                                    "index2_prefix, index2_name, index2_sequence, coordinate, index_type.")

                # Extract information
                index_pairs = [IndexPairForImport(
                                    index1_prefix = str(r[0].value).strip(),
                                    index1_name = str(r[1].value).strip(),
                                    index1_sequence = str(r[2].value).strip().upper(),
                                    index2_prefix = str(r[3].value).strip(),
                                    index2_name = str(r[4].value).strip(),
                                    index2_sequence = str(r[5].value).strip().upper(),
                                    coordinate = str(r[6].value).strip().upper(),
                                    index_type = str(r[7].value).strip())
                                for r in rows]

                # Check that the index types being imported exist in the DB
                index_type_names = set(ip.index_type for ip in index_pairs)
                if IndexType.objects.filter(name__in=index_type_names).count() != len(index_type_names):
                    raise Exception('The file could not be imported because there is at least '
                                    'one invalid value in the "index_type" column')

                # Check that the index sequences being imported contain only relevant characters
                if not re.match(r"^[ATCG]+$", ''.join([(ip.index1_sequence + ip.index2_sequence) for ip in index_pairs])):
                    raise Exception('The file could not be imported because there is at least '
                                    'one invalid value in one of the index sequence column(s)')

                # Check that the coordinates being imported match X00
                if not all(re.match(r"^[A-H]([2-9]|1[0-2]?)$", ip.coordinate) for ip in index_pairs):
                    raise Exception('The file could not be imported because there is at least '
                                    'one invalid value in the "coordinate" column')

                # Import index pairs
                for index_pair in index_pairs:
                    index_type = IndexType.objects.get(name=index_pair.index_type)
                    index1 = IndexI7.objects.create(
                        prefix=index_pair.index1_prefix,
                        number=index_pair.index1_name,
                        index=index_pair.index1_sequence,
                    )
                    index2 = IndexI5.objects.create(
                        prefix=index_pair.index2_prefix,
                        number=index_pair.index2_name,
                        index=index_pair.index2_sequence,
                    )
                    IndexPair.objects.create(
                        index_type=index_type,
                        index1=index1,
                        index2=index2,
                        char_coord=index_pair.coordinate[:1],
                        num_coord=index_pair.coordinate[1:],
                    )

                    # Assign indices to index_type
                    index_type.indices_i7.add(index1)
                    index_type.indices_i5.add(index2)

            except (KeyError, BadZipFile):
                error = "The file could not be imported because it is not in XLSX format."

            except Exception as e:
                error = str(e)

            if error:
                messages.error(request, error)
            else:
                messages.success(request, "The import has been succesful.")

            return HttpResponseRedirect(".")

        model = self.model
        opts = model._meta
        verbose_model_name_plural = opts.verbose_name_plural

        context = {
                'title': verbose_model_name_plural,
                'module_name': 'Index Pairs',
                'site_header': self.admin_site.site_header,
                'has_permission': True,
                'app_label': 'library_sample_shared',
                'opts': opts,
                'site_url': self.admin_site.site_url,
                }

        return render(request, 'admin/import_index_pairs.html', context)


class IndexI5Resource(resources.ModelResource):
    class Meta:
        model = IndexI5
        skip_unchanged = True
        fields = (
            "id",
            "prefix",
            "number",
            "index",
            "index_type__name",
        )


@admin.register(IndexI5)
class IndexI5Admin(ImportExportModelAdmin):
    list_display = ("idx_id", "index", "type", "archived")
    search_fields = (
        "prefix",
        "index",
        "number",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter), ArchivedFilter)

    resource_class = IndexI5Resource

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

    @admin.display(description="Index ID")
    def idx_id(sef, obj):
        return obj.prefix + obj.number


class IndexI7Resource(resources.ModelResource):
    class Meta:
        model = IndexI7
        skip_unchanged = True
        fields = (
            "id",
            "prefix",
            "number",
            "index",
            "index_type__name",
        )


@admin.register(IndexI7)
class IndexI7Admin(ImportExportModelAdmin):
    list_display = ("idx_id", "index", "type", "archived")
    search_fields = (
        "prefix",
        "index",
        "number",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter), ArchivedFilter)

    resource_class = IndexI7Resource

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

    @admin.display(description="Index ID")
    def idx_id(sef, obj):
        return obj.prefix + obj.number


@admin.register(LibraryProtocol)
class LibraryProtocolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "nucleic_acid_type_set",
        "provider",
        "catalog",
        "typical_application",
        "archived",
    )
    search_fields = (
        "name",
        "provider",
        "catalog",
        "typical_application",
    )
    list_filter = ("type", ArchivedFilter)

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

    @admin.display(description="Nucleic Acid Types")
    def nucleic_acid_type_set(self, obj):

        return ", ".join(obj.nucleic_acid_types.all().values_list('name', flat=True))

@admin.register(LibraryType)
class LibraryTypeAdmin(admin.ModelAdmin):
    filter_horizontal = ("library_protocol",)
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
