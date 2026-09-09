from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sample", "0020_alter_sample_library_type"),
    ]

    operations = [
        migrations.RenameField(
            model_name="sample",
            old_name="library_type",
            new_name="analysis_type",
        ),
    ]
