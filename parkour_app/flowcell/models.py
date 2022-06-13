from django.db import models
from django.contrib.postgres.fields import JSONField

from common.models import DateTimeMixin
from request.models import Request
from index_generator.models import Pool


class Sequencer(models.Model):
    name = models.CharField('Name', max_length=50)
    lanes = models.PositiveSmallIntegerField('Number of Lanes')
    lane_capacity = models.PositiveSmallIntegerField('Lane Capacity')
    obsolete = models.PositiveIntegerField("Obsolete", default=1)

    def __str__(self):
        return self.name


class Lane(models.Model):
    name = models.CharField('Name', max_length=6)
    pool = models.ForeignKey(Pool, verbose_name='Pool')
    loading_concentration = models.FloatField(
        'Loading Concentration', blank=True, null=True)
    phix = models.FloatField('PhiX %', blank=True, null=True)
    completed = models.BooleanField('Completed', default=False)

    def __str__(self):
        return f'{self.name}: {self.pool.name}'

    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)

        # When a Lane objects is created, increment the loaded value of the
        # related pool
        if created:
            self.pool.loaded += 1
            self.pool.save(update_fields=['loaded'])


class Flowcell(DateTimeMixin):
    flowcell_id = models.CharField('Flowcell ID', max_length=50, unique=True)
    sequencer = models.ForeignKey(Sequencer, verbose_name='Sequencer')
    lanes = models.ManyToManyField(Lane, related_name='flowcell', blank=True)
    requests = models.ManyToManyField(
        Request, related_name='flowcell', blank=True)
    matrix = JSONField('Flowcell Matrix', blank=True, null=True)
    sequences = JSONField('Sequences', blank=True, null=True)

    def __str__(self):
        return self.flowcell_id
