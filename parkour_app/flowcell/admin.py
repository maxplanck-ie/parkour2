from django.conf import settings
from django.contrib import admin
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
class SequencerAdmin(admin.ModelAdmin):
    list_display = ("name", "lanes", "lane_capacity", "obsolete_name")
    actions = (
        "mark_as_obsolete",
        "mark_as_non_obsolete",
    )

    @admin.action(description="Mark sequencer as obsolete")
    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    @admin.action(description="Mark sequencer as non-obsolete")
    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    @admin.display(description="STATUS")
    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"


@admin.register(Flowcell)
class FlowcellAdmin(admin.ModelAdmin):
    list_display = (
        "flowcell_id",
        "sequencer",
    )
    # search_fields = ('flowcell_id', 'sequencer',)
    list_filter = ("sequencer",)
    exclude = (
        "lanes",
        "requests",
    )
    inlines = [LaneInline]
