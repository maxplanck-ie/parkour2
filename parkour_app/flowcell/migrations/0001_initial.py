# Generated by Django 1.11.4 on 2018-06-11 13:06

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("index_generator", "0001_initial"),
        ("request", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Flowcell",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "flowcell_id",
                    models.CharField(max_length=50, verbose_name="Flowcell ID"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Lane",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=6, verbose_name="Name")),
                (
                    "loading_concentration",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Loading Concentration"
                    ),
                ),
                (
                    "phix",
                    models.FloatField(blank=True, null=True, verbose_name="PhiX %"),
                ),
                (
                    "completed",
                    models.BooleanField(default=False, verbose_name="Completed"),
                ),
                (
                    "pool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="index_generator.Pool",
                        verbose_name="Pool",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Sequencer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                (
                    "lanes",
                    models.PositiveSmallIntegerField(verbose_name="Number of Lanes"),
                ),
                (
                    "lane_capacity",
                    models.PositiveSmallIntegerField(verbose_name="Lane Capacity"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="flowcell",
            name="lanes",
            field=models.ManyToManyField(
                blank=True, related_name="flowcell", to="flowcell.Lane"
            ),
        ),
        migrations.AddField(
            model_name="flowcell",
            name="sequencer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="flowcell.Sequencer",
                verbose_name="Sequencer",
            ),
        ),
        migrations.AddField(
            model_name="flowcell",
            name="create_time",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="Create Time",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="flowcell",
            name="update_time",
            field=models.DateTimeField(auto_now=True, verbose_name="Update Time"),
        ),
        migrations.AddField(
            model_name="flowcell",
            name="requests",
            field=models.ManyToManyField(
                blank=True, related_name="flowcell", to="request.Request"
            ),
        ),
        migrations.AddField(
            model_name="flowcell",
            name="matrix",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, null=True, verbose_name="Flowcell Matrix"
            ),
        ),
        migrations.AlterField(
            model_name="flowcell",
            name="flowcell_id",
            field=models.CharField(
                max_length=50, unique=True, verbose_name="Flowcell ID"
            ),
        ),
        migrations.AddField(
            model_name="flowcell",
            name="sequences",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, null=True, verbose_name="Sequences"
            ),
        ),
    ]