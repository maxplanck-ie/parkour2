from django.db import migrations

VIEW_SQL = """
CREATE OR REPLACE VIEW complete_sample_data AS
SELECT
    s.id AS sample_id,
    s.barcode,
    s.name,
    s.status,
    s.measuring_unit,
    s.sequencing_depth,
    s.measured_value,
    s.gmo,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    nat.id AS nucleic_acid_type_id,
    nat.name AS nucleic_acid_type_name,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    lp2.mean_fragment_size AS average_fragment_size,
    it.name AS index_type_name,
    s.index_reads,
    s.index_i7,
    s.index_i5,
    ip.name AS pool_name
FROM sample_sample AS s
JOIN request_request_samples AS rl ON s.id = rl.sample_id
JOIN request_request AS r ON rl.request_id = r.id
LEFT JOIN sample_nucleicacidtype AS nat ON s.nucleic_acid_type_id = nat.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON s.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON s.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON s.index_type_id = it.id
LEFT JOIN index_generator_pool_samples AS ips ON s.id = ips.sample_id
LEFT JOIN index_generator_pool AS ip ON ips.pool_id = ip.id
LEFT JOIN library_preparation_librarypreparation AS lp2 ON lp2.sample_id = s.id;
"""

class Migration(migrations.Migration):

    dependencies = [
        ("library_sample_shared", "0014_alter_historicallibraryprotocol_name_and_more"),
        ("sample", "0011_alter_sample_measuring_unit_and_more"),
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL,
            reverse_sql="DROP VIEW IF EXISTS complete_sample_data;"
        ),
    ]