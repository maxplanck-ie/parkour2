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
    l.measured_value,
    l.percent_total,
    l.size_distribution_facility AS average_fragment_size,
    l.measured_value_facility AS concentration_library,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    it.name AS index_type_name,
    l.index_i7,
    l.index_i5,
    i7.id AS i7_id,
    i5.id AS i5_id,
    (ip.char_coord || ip.num_coord) AS coordinate,
    l.read_length_id,
    rl.name AS read_length_name,
    igp.name AS pool_name
FROM library_library AS l
JOIN request_request_libraries AS rrl ON l.id = rrl.library_id
JOIN request_request AS r ON rrl.request_id = r.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON l.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON l.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON l.index_type_id = it.id
LEFT JOIN index_generator_pool_libraries AS ipl ON l.id = ipl.library_id
LEFT JOIN index_generator_pool AS igp ON ipl.pool_id = igp.id
LEFT JOIN library_sample_shared_readlength AS rl ON l.read_length_id = rl.id
LEFT JOIN library_sample_shared_indexi7 AS i7 ON i7.index = l.index_i7
LEFT JOIN library_sample_shared_indexi5 AS i5 ON i5.index = l.index_i5
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("library_sample_shared", "0014_alter_historicallibraryprotocol_name_and_more"),
        (
            "library",
            "0007_rename_amplification_cycles_library_removed_amplification_cycles_and_more",
        ),
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS complete_library_data;"
        ),
    ]
