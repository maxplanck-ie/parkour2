import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0013_historicalrequest_related_requests"),
    ]

    operations = [
        migrations.AddField(
            model_name="filerequest",
            name="file_type",
            field=models.CharField(
                default="Other",
                max_length=100,
                validators=[
                    django.core.validators.RegexValidator(
                        message=(
                            "Use letters and numbers separated by single underscores; "
                            "spaces are not allowed."
                        ),
                        regex="^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$",
                    )
                ],
                verbose_name="File Type",
            ),
        ),
    ]
