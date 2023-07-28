from common.models import DateTimeMixin
from django.db import models
from index_generator.models import Pool
from request.models import Request


class Sequencer(models.Model):
    name = models.CharField("Name", max_length=50)
    obsolete = models.PositiveIntegerField("Obsolete", default=1)

    instrument_platform = models.CharField(
        "instrument platform", help_text='For samplesheet', max_length=50)
    instrument_type = models.CharField(
        "instrument type", help_text='For samplesheet', max_length=50)
    bclconvert_version = models.CharField(
        "BCLconvert version", help_text='For samplesheet', max_length=50)

    def __str__(self):
        return self.name


class Lane(models.Model):
    name = models.CharField("Name", max_length=6)
    pool = models.ForeignKey(
        Pool, verbose_name="Pool", on_delete=models.SET_NULL, null=True
    )
    loading_concentration = models.FloatField(
        "Loading Concentration", blank=True, null=True
    )
    phix = models.FloatField("PhiX %", blank=True, null=True)
    completed = models.BooleanField("Completed", default=False)

    def __str__(self):
        return f"{self.name}: {self.pool.name}"

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        # When a Lane objects is created, increment the loaded value of the
        # related pool
        if created:
            self.pool.loaded += 1
            self.pool.save(update_fields=["loaded"])


class Flowcell(DateTimeMixin):
    flowcell_id = models.CharField("Flowcell ID", max_length=50, unique=True)
    pool_size = models.ForeignKey(
        'index_generator.PoolSize',
        verbose_name="Pool Size",
        on_delete=models.SET_NULL, null=True
    )
    lanes = models.ManyToManyField(Lane, related_name="flowcell", blank=True)
    requests = models.ManyToManyField(Request, related_name="flowcell", blank=True)
    matrix = models.JSONField("Flowcell Matrix", blank=True, null=True)
    sequences = models.JSONField("Sequences", blank=True, null=True)

    run_name = models.CharField("run name", help_text='For samplesheet', max_length=200)
    read1_cycles = models.PositiveSmallIntegerField("read 1 cycles")
    read2_cycles = models.PositiveSmallIntegerField("read 2 cycles")
    index1_cycles = models.PositiveSmallIntegerField("index 1 cycles")
    index2_cycles = models.PositiveSmallIntegerField("index 2 cycles")
    library_prep_kits = models.CharField("library prep kits", help_text='For samplesheet', max_length=200, blank=True)

    def __str__(self):
        return self.flowcell_id
