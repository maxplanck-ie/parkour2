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
    ip.name AS pool_name
FROM library_library AS l
JOIN request_request_libraries AS rl ON l.id = rl.library_id
JOIN request_request AS r ON rl.request_id = r.id
LEFT JOIN library_sample_shared_organism AS o ON l.organism_id = o.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON l.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON l.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON l.index_type_id = it.id
LEFT JOIN index_generator_pool_libraries AS ipl ON l.id = ipl.library_id
LEFT JOIN index_generator_pool AS ip ON ipl.pool_id = ip.id;
"""

class Migration(migrations.Migration):

    dependencies = [
        ("library_sample_shared", "0014_alter_historicallibraryprotocol_name_and_more"),
        ("library", "0007_rename_amplification_cycles_library_removed_amplification_cycles_and_more"),
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL,
            reverse_sql="DROP VIEW IF EXISTS complete_library_data;"
        ),
    ]