# Date column of complete_library_data_mv now shows the most advanced request
# timestamp available (submission > approval > creation); repopulate.

from django.db import migrations

from common.sql import library_insert_sql_from_select, library_select_sql

POPULATE_SQL = library_insert_sql_from_select(library_select_sql())


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0015_complete_library_data_flowcell_create_times"),
        ("request", "0016_request_submitted_at"),
    ]

    operations = [
        migrations.RunSQL(
            sql="TRUNCATE TABLE complete_library_data_mv;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=POPULATE_SQL,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
