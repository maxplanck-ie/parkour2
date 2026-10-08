from common.admin import ArchivedFilter
from common.guarded_delete import ReferencedGuardedDeleteMixin
from common.utils import set_archived
from django.conf import settings
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from flowcell.models import Flowcell, Sequencer


class LaneInline(admin.TabularInline):
    model = Flowcell.lanes.through
    verbose_name = "Lane"
    verbose_name_plural = "Lanes"
    # readonly_fields = ('lane',)
    can_delete = False
    extra = 0

    fields = (
        "name",
        "pool",
        "loading_concentration",
        "phix",
        "completed",
    )
    readonly_fields = (
        "name",
        "pool",
        "loading_concentration",
        "phix",
        "completed",
    )

    @admin.display(description="Name")
    def name(self, instance):
        return instance.lane.name

    @admin.display(description="Pool")
    def pool(self, instance):
        return instance.lane.pool.name

    @admin.display(description="Loading Concentration")
    def loading_concentration(self, instance):
        return instance.lane.loading_concentration

    @admin.display(description="PhiX %")
    def phix(self, instance):
        return instance.lane.phix

    @admin.display(
        description="Completed",
        boolean=True,
    )
    def completed(self, instance):
        return instance.lane.completed

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sequencer)
class SequencerAdmin(ReferencedGuardedDeleteMixin, SimpleHistoryAdmin):
    list_display = ("name", "lanes", "lane_capacity", "archived")

    list_filter = (ArchivedFilter,)

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
        "delete_guarded",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        set_archived(queryset, True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        set_archived(queryset, False)


@admin.register(Flowcell)
class FlowcellAdmin(admin.ModelAdmin):
    list_display = ("flowcell_id", "sequencer", "archived")
    # search_fields = ('flowcell_id', 'sequencer',)
    list_filter = ("sequencer", ArchivedFilter)
    exclude = (
        "lanes",
        "requests",
    )
    inlines = [LaneInline]

    actions = (
        "mark_as_archived",
        "mark_as_non_archived",
    )

    @admin.action(description="Mark as archived")
    def mark_as_archived(self, request, queryset):
        set_archived(queryset, True)

    @admin.action(description="Mark as non-archived")
    def mark_as_non_archived(self, request, queryset):
        set_archived(queryset, False)
