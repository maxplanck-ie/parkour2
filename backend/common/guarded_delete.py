from common.utils import set_archived
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.db import transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse


class GuardedDeleteMixin:
    """Replace plain deletion of records with archive-or-delete.

    Used records (see is_used()) are never deleted: they are archived. Unused
    records are archived too, unless the user ticks the "permanent delete" box
    on the confirmation page (meant for failed imports).

    Subclasses implement is_used(), archive_queryset() and, if a plain
    obj.delete() is not enough, hard_delete().
    """

    delete_confirmation_template = "admin/common/guarded_delete_confirmation.html"

    # Extra sentence for the permanent-delete checkbox label, if deleting
    # also cleans up related records.
    permanent_delete_note = ""

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
            "permanent_delete_note": self.permanent_delete_note,
            "bulk": bulk,
        }

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is None or not self.has_delete_permission(request, obj):
            return super().delete_view(request, object_id, extra_context)

        if request.method == "POST" and "post" in request.POST:
            if self.is_used(obj) or not request.POST.get("confirm_permanent_delete"):
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


class ReferencedGuardedDeleteMixin(GuardedDeleteMixin):
    """Guarded delete for catalog records (organisms, protocols, sequencers…).

    A record counts as used when any row still points at it through a foreign
    key, one-to-one or many-to-many relation. Used records are only ever
    archived, so the pages and exports that list them keep working. Relations
    are discovered from the model itself, so a foreign key added later is
    covered without touching the admin.
    """

    def is_used(self, obj):
        for rel in obj._meta.related_objects:
            related = rel.related_model
            if related._default_manager.filter(**{rel.field.name: obj}).exists():
                return True
        return False

    def archive_queryset(self, queryset):
        set_archived(queryset, True)
