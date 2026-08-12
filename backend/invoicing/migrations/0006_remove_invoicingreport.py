from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("invoicing", "0005_archived_feature"),
    ]

    operations = [
        migrations.DeleteModel(
            name="InvoicingReport",
        ),
    ]
