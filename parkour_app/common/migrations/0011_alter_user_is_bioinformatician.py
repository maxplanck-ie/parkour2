# Generated by Django 3.2.15 on 2022-09-12 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0010_alter_principalinvestigator_parent_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_bioinformatician',
            field=models.BooleanField(default=False, help_text='Designates whether a user belongs to Bioinformatics service.', verbose_name='Bioinformatician status'),
        ),
    ]