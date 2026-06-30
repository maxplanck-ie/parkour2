from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0011_request_change_ownership_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="related_requests",
            field=models.ManyToManyField(
                blank=True,
                related_name="related_to_requests",
                to="request.request",
            ),
        ),
    ]
