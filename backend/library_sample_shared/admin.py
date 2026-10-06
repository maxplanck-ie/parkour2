import re
from dataclasses import dataclass
from zipfile import BadZipFile

from common.admin import ArchivedFilter
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path, resolve, reverse
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from simple_history.admin import SimpleHistoryAdmin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from openpyxl import load_workbook

from .forms import IndexTypeForm
from .models import (
    ConcentrationMethod,
    IndexI5,
    IndexI7,
    IndexPair,
    IndexType,
    LibraryProtocol,
    AnalysisType,
    Organism,
    ReadLength,
)
from .utils import (
    archive_index_pairs,
    archive_index_types,
    delete_index,
    delete_index_pair,
    delete_index_type,
    index_has_used_pair,
    index_is_used,
    index_pair_is_used,
    index_type_is_used,
)


@admin.register(Organism)
class OrganismAdmin(SimpleHistoryAdmin):
    list_display = ("name", "label", "yaml")

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
        args = resolve(request.path_info).args
        index_type_id = args[0] if args else None

        if db_field.name == "index1":
            kwargs["queryset"] = IndexI7.objects.filter(
                archived=False, index_type__id=index_type_id
            )

        elif db_field.name == "index2":
            kwargs["queryset"] = IndexI5.objects.filter(
                archived=False, index_type__id=index_type_id
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GuardedDeleteMixin:
    """Replace plain deletion of index records with archive-or-delete.

    Records used by a Library/Sample at status >= Sequencing are never deleted:
    they are archived. Unused records are archived too, unless the user ticks the
    "permanent delete" box on the confirmation page (meant for failed imports).

    Subclasses implement is_used(), archive_queryset() and, if a plain
    obj.delete() is not enough, hard_delete().
    """

    delete_confirmation_template = (
        "admin/library_sample_shared/guarded_delete_confirmation.html"
    )

    # Subclasses set True when a confirmed permanent delete may remove even
    # records whose sequence is used at status >= Sequencing; their indices
    # stay protected (archived) via hard_delete() instead.
    deletable_when_used = False

    def is_used(self, obj):
        raise NotImplementedError

    def archive_queryset(self, queryset):
        raise NotImplementedError

    def hard_delete(self, obj):
        obj.delete()

    def impact_summary(self, objs):
        """(label, count) rows describing what else permanent deletion removes."""
        return []

    def delete_model(self, request, obj):
        self.hard_delete(obj)

    def get_actions(self, request):
        # Django's delete_selected would bypass the guard.
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def _split(self, objs):
        used, unused = [], []
        for obj in objs:
            (used if self.is_used(obj) else unused).append(obj)
        return used, unused

    def _confirm_context(self, objs, bulk):
        used, unused = self._split(objs)
        return {
            "used_objects": used,
            "unused_objects": unused,
            "impact": self.impact_summary(unused),
            "deletable_when_used": self.deletable_when_used,
            "bulk": bulk,
        }

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is None or not self.has_delete_permission(request, obj):
            return super().delete_view(request, object_id, extra_context)

        if request.method == "POST" and "post" in request.POST:
            if (
                self.is_used(obj) and not self.deletable_when_used
            ) or not request.POST.get("confirm_permanent_delete"):
                self.archive_queryset(self.model.objects.filter(pk=obj.pk))
                self.message_user(
                    request,
                    f"{self.opts.verbose_name.capitalize()} “{obj}” was archived, "
                    "not deleted.",
                    messages.SUCCESS,
                )
                return HttpResponseRedirect(
                    reverse(
                        f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
                    )
                )
            return super().delete_view(request, object_id, extra_context)

        context = {**self._confirm_context([obj], bulk=False), **(extra_context or {})}
        return super().delete_view(request, object_id, context)

    @admin.action(
        description="Delete selected (archives if in use)", permissions=["delete"]
    )
    def delete_guarded(self, request, queryset):
        objs = list(queryset)
        if not request.POST.get("post"):
            context = {
                **self.admin_site.each_context(request),
                **self._confirm_context(objs, bulk=True),
                "title": "Are you sure?",
                "opts": self.opts,
                "queryset": queryset,
                "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
                "action_name": "delete_guarded",
            }
            return TemplateResponse(request, self.delete_confirmation_template, context)

        used, unused = self._split(objs)
        confirmed = bool(request.POST.get("confirm_permanent_delete"))
        if self.deletable_when_used:
            to_delete = objs if confirmed else []
            to_archive = [] if confirmed else objs
        else:
            to_archive = used if confirmed else objs
            to_delete = unused if confirmed else []
        with transaction.atomic():
            if to_archive:
                self.archive_queryset(
                    self.model.objects.filter(pk__in=[o.pk for o in to_archive])
                )
            if to_delete:
                self.log_deletions(request, to_delete)
                for obj in to_delete:
                    self.hard_delete(obj)
        self.message_user(
            request,
            f"Archived {len(to_archive)}, permanently deleted {len(to_delete)}.",
            messages.SUCCESS,
        )


@admin.register(IndexType)
class IndexTypeAdmin(GuardedDeleteMixin, ImportExportModelAdmin):
    form = IndexTypeForm

    list_display = ("name", "is_dual", "format", "archived")

    list_filter = (ArchivedFilter,)

    # filter_horizontal used to render every IndexI7/IndexI5 row as an
    # <option>, which becomes unusable once labs have 1000+ indices in
    # their catalog. autocomplete_fields loads matches on demand via
    # IndexI7Admin/IndexI5Admin.search_fields instead.
    autocomplete_fields = (
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
        "delete_guarded",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        archive_index_types(queryset)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        queryset.update(archived=False)

    def is_used(self, obj):
        return index_type_is_used(obj)

    def archive_queryset(self, queryset):
        archive_index_types(queryset)

    def hard_delete(self, obj):
        delete_index_type(obj)

    def impact_summary(self, objs):
        return [
            ("Index pairs", IndexPair.objects.filter(index_type__in=objs).count()),
        ]

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
class IndexPairAdmin(GuardedDeleteMixin, admin.ModelAdmin):
    list_display = ("index_pair", "coordinate", "archived")
    search_fields = ("index_type__name",)
    list_filter = ("index_type", ArchivedFilter)

    # A pair is a plate coordinate entry: sequenced records hold sequences, not
    # pair FKs, so a confirmed delete may remove the pair itself.
    # delete_index_pair() archives its in-use indices instead of deleting them.
    deletable_when_used = True

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
        "delete_guarded",
    )

    def hard_delete(self, obj):
        delete_index_pair(obj)

    def is_used(self, obj):
        return index_pair_is_used(obj)

    def archive_queryset(self, queryset):
        archive_index_pairs(queryset)

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        archive_index_pairs(queryset)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        # Get the IDs and index types before updating
        index_pair_ids = list(queryset.values_list("id", flat=True))
        affected_index_types = set(queryset.values_list("index_type", flat=True))
        queryset.update(archived=False)

        # Fetch fresh objects with related fields
        for obj in IndexPair.objects.select_related("index1", "index2").filter(
            id__in=index_pair_ids,
        ):
            if obj.index1 and obj.index1.archived:
                obj.index1.archived = False
                obj.index1.save(update_fields=["archived"])
            if obj.index2 and obj.index2.archived:
                obj.index2.archived = False
                obj.index2.save(update_fields=["archived"])

        # Unarchive associated IndexTypes if they were archived
        for index_type_id in affected_index_types:
            if index_type_id:  # Make sure it's not None
                IndexType.objects.filter(id=index_type_id, archived=True).update(
                    archived=False
                )

    def index_pair(self, obj):
        return str(obj)

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields[
            "index_type"
        ].queryset = IndexType.objects.filter(archived=False, format="plate")
        return super().render_change_form(request, context, args, kwargs)

    def get_urls(self):
        return [
            path(
                "import_plate_pairs/",
                self.admin_site.admin_view(self.import_index_pairs),
            ),
            *super().get_urls(),
        ]

    def import_index_pairs(self, request):
        error = ""

        # Import Index Pairs from an Excel spreadsheet

        # If the form has been posted
        if request.method == "POST":
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
                wb = load_workbook(filename=request.FILES["file"].file)

                # Check that file contains only one worksheet
                if len(wb.worksheets) > 1:
                    raise Exception(
                        "The file could not be imported because it contains more than one sheet."
                    )

                # Load first sheet
                sheet = wb.worksheets[0]

                # Get rows
                rows = iter(sheet)

                # Get table header
                header = next(rows)
                header_values = [
                    str(cell.value).strip().lower() for cell in header if cell.value
                ]

                # Check that column headers are named and ordered as expected
                expected_header_values = [
                    "index1_prefix",
                    "index1_name",
                    "index1_sequence",
                    "index2_prefix",
                    "index2_name",
                    "index2_sequence",
                    "coordinate",
                    "index_type",
                ]
                if header_values != expected_header_values:
                    raise Exception(
                        "The file could not be imported because the column titles do not "
                        "match the expected values: index1_prefix, index1_name, index1_sequence, "
                        "index2_prefix, index2_name, index2_sequence, coordinate, index_type."
                    )

                # Extract information
                index_pairs = [
                    IndexPairForImport(
                        index1_prefix=str(r[0].value).strip(),
                        index1_name=str(r[1].value).strip(),
                        index1_sequence=str(r[2].value).strip().upper(),
                        index2_prefix=str(r[3].value).strip(),
                        index2_name=str(r[4].value).strip(),
                        index2_sequence=str(r[5].value).strip().upper(),
                        coordinate=str(r[6].value).strip().upper(),
                        index_type=str(r[7].value).strip(),
                    )
                    for r in rows
                ]

                # Check that the index types being imported exist in the DB
                index_type_names = {ip.index_type for ip in index_pairs}
                if IndexType.objects.filter(name__in=index_type_names).count() != len(
                    index_type_names
                ):
                    raise Exception(
                        "The file could not be imported because there is at least "
                        'one invalid value in the "index_type" column'
                    )

                # Check that the index sequences being imported contain only relevant characters
                if not re.match(
                    r"^[ATCG]+$",
                    "".join(
                        [
                            (ip.index1_sequence + ip.index2_sequence)
                            for ip in index_pairs
                        ]
                    ),
                ):
                    raise Exception(
                        "The file could not be imported because there is at least "
                        "one invalid value in one of the index sequence column(s)"
                    )

                # Check that the coordinates being imported match X00
                if not all(
                    re.match(r"^[A-H]([2-9]|1[0-2]?)$", ip.coordinate)
                    for ip in index_pairs
                ):
                    raise Exception(
                        "The file could not be imported because there is at least "
                        'one invalid value in the "coordinate" column'
                    )

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
                error = (
                    "The file could not be imported because it is not in XLSX format."
                )

            except Exception as e:
                error = str(e)

            if error:
                messages.error(request, error)
            else:
                messages.success(request, "The import has been successful.")

            return HttpResponseRedirect(".")

        model = self.model
        opts = model._meta
        verbose_model_name_plural = opts.verbose_name_plural

        context = {
            "title": verbose_model_name_plural,
            "module_name": "Index Pairs",
            "site_header": self.admin_site.site_header,
            "has_permission": True,
            "app_label": "library_sample_shared",
            "opts": opts,
            "site_url": self.admin_site.site_url,
        }

        return render(request, "admin/import_plate_pairs.html", context)


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
class IndexI5Admin(GuardedDeleteMixin, ImportExportModelAdmin):
    list_display = ("idx_id", "index", "type", "archived")
    search_fields = (
        "index",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter), ArchivedFilter)

    resource_class = IndexI5Resource

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
        "delete_guarded",
    )

    def is_used(self, obj):
        return index_is_used(obj) or index_has_used_pair(obj)

    def archive_queryset(self, queryset):
        queryset.update(archived=True)

    def hard_delete(self, obj):
        delete_index(obj)

    def impact_summary(self, objs):
        return [("Index pairs", IndexPair.objects.filter(index2__in=objs).count())]

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
class IndexI7Admin(GuardedDeleteMixin, ImportExportModelAdmin):
    list_display = ("idx_id", "index", "type", "archived")
    search_fields = (
        "index",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter), ArchivedFilter)

    resource_class = IndexI7Resource

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
        "delete_guarded",
    )

    def is_used(self, obj):
        return index_is_used(obj) or index_has_used_pair(obj)

    def archive_queryset(self, queryset):
        queryset.update(archived=True)

    def hard_delete(self, obj):
        delete_index(obj)

    def impact_summary(self, objs):
        return [("Index pairs", IndexPair.objects.filter(index1__in=objs).count())]

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
class LibraryProtocolAdmin(SimpleHistoryAdmin):
    list_display = (
        "name",
        "type",
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


@admin.register(AnalysisType)
class AnalysisTypeAdmin(SimpleHistoryAdmin):
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
