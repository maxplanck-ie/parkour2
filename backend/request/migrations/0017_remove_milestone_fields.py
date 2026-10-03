from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0016_request_submitted_at"),
    ]

    operations = [
        migrations.RemoveField(model_name="request", name="flowcell_loaded_at"),
        migrations.RemoveField(model_name="request", name="qc_completed_at"),
        migrations.RemoveField(
            model_name="historicalrequest", name="flowcell_loaded_at"
        ),
        migrations.RemoveField(model_name="historicalrequest", name="qc_completed_at"),
    ]
