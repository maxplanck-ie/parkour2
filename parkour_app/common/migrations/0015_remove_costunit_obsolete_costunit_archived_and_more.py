# Generated by Django 4.2.6 on 2023-10-16 11:59

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0014_auto_20221031_1657'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='costunit',
            name='obsolete',
        ),
        migrations.AddField(
            model_name='costunit',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
        migrations.AddField(
            model_name='organization',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
        migrations.CreateModel(
            name='Duty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(default=datetime.datetime.now, verbose_name='Start Date')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='End Date')),
                ('facility', models.CharField(choices=[('bioinfo', 'BioInfo'), ('deepseq', 'DeepSeq')], default='bioinfo', max_length=7, verbose_name='Facility')),
                ('platform', models.CharField(choices=[('short', 'Short'), ('long', 'Long')], default='short', max_length=5, verbose_name='Platform')),
                ('comment', models.TextField(blank=True, max_length=2500, null=True, verbose_name='Comment')),
                ('archived', models.BooleanField(default=False, verbose_name='Archived')),
                ('backup_name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='backup_name', to=settings.AUTH_USER_MODEL, verbose_name='Backup Person')),
                ('main_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='main_name', to=settings.AUTH_USER_MODEL, verbose_name='Responsible Person')),
            ],
            options={
                'verbose_name': 'Duty',
                'verbose_name_plural': 'Duties',
                'db_table': 'duty',
                'ordering': ['end_date', 'start_date'],
            },
        ),
    ]