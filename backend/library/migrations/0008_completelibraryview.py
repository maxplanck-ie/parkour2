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
    r.name AS request_name,
    o.name AS organism_name,
    lp.name AS library_protocol_name,
    lt.name AS library_type_name,
    it.name AS index_type_name,
    l.index_reads,
    l.index_i7,
    l.index_i5,
    rl.created_at AS request_library_created_at
FROM library_library AS l
JOIN request_request_libraries AS rl ON l.id = rl.library_id
JOIN request_request AS r ON rl.request_id = r.id
LEFT JOIN common_organism AS o ON l.organism_id = o.id
LEFT JOIN common_libraryprotocol AS lp ON l.library_protocol_id = lp.id
LEFT JOIN common_librarytype AS lt ON l.library_type_id = lt.id
LEFT JOIN common_indextype AS it ON l.index_type_id = it.id;
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