from django.contrib import admin
from flowcell.models import Sequencer, Flowcell
from django.conf import settings

class LaneInline(admin.TabularInline):
    model = Flowcell.lanes.through
    verbose_name = 'Lane'
    verbose_name_plural = 'Lanes'
    # readonly_fields = ('lane',)
    can_delete = False
    extra = 0

    fields = ('name', 'pool', 'loading_concentration', 'phix', 'completed',)
    readonly_fields = ('name', 'pool', 'loading_concentration', 'phix',
                       'completed',)

    def name(self, instance):
        return instance.lane.name
    name.short_description = 'Name'

    def pool(self, instance):
        return instance.lane.pool.name
    pool.short_description = 'Pool'

    def loading_concentration(self, instance):
        return instance.lane.loading_concentration
    loading_concentration.short_description = 'Loading Concentration'

    def phix(self, instance):
        return instance.lane.phix
    phix.short_description = 'PhiX %'

    def completed(self, instance):
        return instance.lane.completed
    completed.short_description = 'Completed'
    completed.boolean = True

    def has_add_permission(self, request):
        return False


@admin.register(Sequencer)
class SequencerAdmin(admin.ModelAdmin):
    list_display = ('name', 'lanes', 'lane_capacity','obsolete_name')
    actions = ('mark_as_obsolete', 'mark_as_non_obsolete',)

    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    mark_as_obsolete.short_description = "Mark sequencer as obsolete"

    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    mark_as_non_obsolete.short_description = "Mark sequencer as non-obsolete"

    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"

    obsolete_name.short_description = "STATUS"


@admin.register(Flowcell)
class FlowcellAdmin(admin.ModelAdmin):
    list_display = ('flowcell_id', 'sequencer',)
    # search_fields = ('flowcell_id', 'sequencer',)
    list_filter = ('sequencer',)
    exclude = ('lanes', 'requests',)
    inlines = [LaneInline]
