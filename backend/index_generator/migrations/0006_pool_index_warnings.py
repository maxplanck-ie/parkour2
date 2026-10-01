from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("index_generator", "0005_archived_feature"),
    ]

    operations = [
        migrations.AddField(
            model_name="pool",
            name="index_warnings",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Index warnings"
            ),
        ),
    ]
