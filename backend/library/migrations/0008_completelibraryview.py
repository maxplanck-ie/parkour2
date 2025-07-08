from django.db import migrations

VIEW_SQL = """
CREATE OR REPLACE VIEW complete_library_data AS
SELECT
    l.id AS library_id,
    l.barcode,
    l.name,
    l.status,
    l.sequencing_depth,
    l.measuring_unit,
    l.mean_fragment_size,
    l.percent_total,
    l.measuring_unit_facility,
    r.id AS request_id,
    r.name AS request_name
FROM library_library AS l
JOIN request_request_libraries AS rl ON l.id = rl.library_id
JOIN request_request AS r ON rl.request_id = r.id;
"""

class Migration(migrations.Migration):

    dependencies = [
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL,
            reverse_sql="DROP VIEW IF EXISTS complete_library_data;"
        ),
    ]