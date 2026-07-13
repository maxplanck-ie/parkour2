from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0019_runstats_sequencestats_templates"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="runstatisticstemplate",
            options={
                "verbose_name": "Runs Statistics Template",
                "verbose_name_plural": "Templates -> Runs Statistics",
            },
        ),
        migrations.AlterModelOptions(
            name="sequencesstatisticstemplate",
            options={
                "verbose_name": "Sequenced Samples Statistics Template",
                "verbose_name_plural": "Templates -> Sequenced Samples Statistics",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalrunstatisticstemplate",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical Runs Statistics Template",
                "verbose_name_plural": "historical Templates -> Runs Statistics",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalsequencesstatisticstemplate",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical Sequenced Samples Statistics Template",
                "verbose_name_plural": "historical Templates -> Sequenced Samples Statistics",
            },
        ),
    ]
