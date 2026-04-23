from django.db import migrations, models


SAMPLE_MEASURING_UNIT_CHOICES = [
    ("ng/\u00b5l", "ng/\u00b5l (Concentration)"),
    ("Cells", "Cells"),
    ("k", "k (Cells)"),
    ("M", "M (Cells)"),
    ("Unknown", "Unknown"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("sample", "0015_complete_sample_data_comment_input_organism_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sample",
            name="measuring_unit",
            field=models.CharField(
                blank=True,
                choices=SAMPLE_MEASURING_UNIT_CHOICES,
                max_length=50,
                null=True,
                verbose_name="Measuring Unit",
            ),
        ),
        migrations.AlterField(
            model_name="sample",
            name="measuring_unit_facility",
            field=models.CharField(
                blank=True,
                choices=SAMPLE_MEASURING_UNIT_CHOICES,
                max_length=50,
                null=True,
                verbose_name="Measuring Unit (facility)",
            ),
        ),
    ]
