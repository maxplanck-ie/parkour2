import django.contrib.postgres.fields
from django.db import migrations, models

from common.sql import library_insert_sql_from_select, library_select_sql


POPULATE_SQL = library_insert_sql_from_select(library_select_sql())


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0014_alter_library_index_fields_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
ALTER TABLE complete_library_data_mv
ADD COLUMN IF NOT EXISTS flowcell_create_times TIMESTAMP WITH TIME ZONE[];
TRUNCATE TABLE complete_library_data_mv;
""",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=POPULATE_SQL,
                    reverse_sql="TRUNCATE TABLE complete_library_data_mv;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="completelibrarydata",
                    name="flowcell_create_times",
                    field=django.contrib.postgres.fields.ArrayField(
                        base_field=models.DateTimeField(), null=True, size=None
                    ),
                ),
            ],
        ),
    ]
