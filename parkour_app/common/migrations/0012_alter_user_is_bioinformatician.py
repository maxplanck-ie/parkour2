# Generated by Django 3.2.15 on 2022-09-12 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0011_alter_user_is_bioinformatician'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_bioinformatician',
            field=models.BooleanField(default=False, help_text='Designates whether a user is a bioinformatician.', verbose_name='Bioinformatician status'),
        ),
    ]