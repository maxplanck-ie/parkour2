# Generated by Django 3.2.14 on 2022-08-18 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0003_auto_20220818_1435'),
        ('sample', '0004_auto_20220818_1435'),
        ('pooling', '0002_pooling_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pooling',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='pooling',
            name='library',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='library.library', verbose_name='Library'),
        ),
        migrations.AlterField(
            model_name='pooling',
            name='sample',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sample.sample', verbose_name='Sample'),
        ),
    ]