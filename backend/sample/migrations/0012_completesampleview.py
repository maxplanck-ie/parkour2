from django.db import migrations

VIEW_SQL = """
CREATE OR REPLACE VIEW complete_sample_data AS
SELECT
    s.id AS sample_id,
    s.barcode,
    s.name,
    s.status,
    s.sequencing_depth,
    nat.id AS nucleic_acid_type_id,
    nat.name AS nucleic_acid_type_name,
    s.measuring_unit,
    s.measured_value,
    s.gmo,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    lp2.mean_fragment_size AS average_fragment_size,
    lp2.starting_amount,
    lp2.pcr_cycles,
    lp2.concentration_library,
    it.name AS index_type_name,
    s.index_i7,
    s.index_i5,
    i7.id AS i7_id,
    i5.id AS i5_id,
    (ip.char_coord || ip.num_coord) AS coordinate,
    s.read_length_id,
    rl.name AS read_length_name,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    igp.name AS pool_name
FROM sample_sample AS s
JOIN request_request_samples AS rrs ON s.id = rrs.sample_id
JOIN request_request AS r ON rrs.request_id = r.id
LEFT JOIN sample_nucleicacidtype AS nat ON s.nucleic_acid_type_id = nat.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON s.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON s.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON s.index_type_id = it.id
LEFT JOIN index_generator_pool_samples AS ips ON s.id = ips.sample_id
LEFT JOIN index_generator_pool AS igp ON ips.pool_id = igp.id
LEFT JOIN library_preparation_librarypreparation AS lp2 ON lp2.sample_id = s.id
LEFT JOIN library_sample_shared_readlength AS rl ON s.read_length_id = rl.id
LEFT JOIN library_sample_shared_indexi7 AS i7 ON i7.index = s.index_i7
LEFT JOIN library_sample_shared_indexi5 AS i5 ON i5.index = s.index_i5
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("library_sample_shared", "0014_alter_historicallibraryprotocol_name_and_more"),
        ("sample", "0011_alter_sample_measuring_unit_and_more"),
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS complete_sample_data;"
        ),
    ]
