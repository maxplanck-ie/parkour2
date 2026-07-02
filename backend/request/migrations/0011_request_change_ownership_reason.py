from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0010_request_milestones"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="change_ownership_reason",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="Change Ownership Comment",
            ),
        ),
        migrations.AddField(
            model_name="historicalrequest",
            name="change_ownership_reason",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="Change Ownership Comment",
            ),
        ),
    ]
