# Generated by Django 4.2.6 on 2023-10-16 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowcell', '0006_auto_20230702_1816'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sequencer',
            name='obsolete',
        ),
        migrations.AddField(
            model_name='flowcell',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
        migrations.AddField(
            model_name='sequencer',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
    ]