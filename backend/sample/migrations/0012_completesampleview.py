from django.db import migrations

VIEW_SQL = """
CREATE OR REPLACE VIEW complete_sample_data AS
SELECT DISTINCT ON (s.id)
    s.id AS sample_id,
    s.barcode,
    s.name,
    s.status,
    s.sequencing_depth,
    s.measuring_unit,
    s.measured_value,
    s.gmo,
    s.index_i7,
    s.index_i5,
    s.read_length_id,
    nat.id AS nucleic_acid_type_id,
    nat.name AS nucleic_acid_type_name,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    lp2.mean_fragment_size AS average_fragment_size,
    lp2.starting_amount,
    lp2.pcr_cycles,
    lp2.concentration_library,
    i7.prefix || i7.number AS i7_id,
    i5.prefix || i5.number AS i5_id,
    ip.char_coord || ip.num_coord::text AS coordinate,
    it.name AS index_type_name,
    rl.name AS read_length_name,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    pools.pool_names,
    fcids.flowcell_ids,
    fcids.sequencer_names,
    fcids.sequencer_ids
FROM sample_sample AS s
JOIN request_request_samples AS rrs ON s.id = rrs.sample_id
JOIN request_request AS r ON rrs.request_id = r.id
LEFT JOIN sample_nucleicacidtype AS nat ON s.nucleic_acid_type_id = nat.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON s.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON s.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON s.index_type_id = it.id
LEFT JOIN library_preparation_librarypreparation AS lp2 ON lp2.sample_id = s.id
LEFT JOIN library_sample_shared_readlength AS rl ON s.read_length_id = rl.id
LEFT JOIN library_sample_shared_indexi7 AS i7 ON i7.index = s.index_i7
LEFT JOIN library_sample_shared_indexi5 AS i5 ON i5.index = s.index_i5
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id
    AND ip.index2_id = i5.id

-- pools array (sample -> pool samples)
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT p.name) AS pool_names
    FROM index_generator_pool_samples ps
    JOIN index_generator_pool p ON ps.pool_id = p.id
    WHERE ps.sample_id = s.id
) pools ON TRUE

-- flowcells & sequencers via correct lane & m2m tables
LEFT JOIN LATERAL (
    SELECT
        array_agg(DISTINCT fc.flowcell_id) AS flowcell_ids,
        array_agg(DISTINCT seq.name) AS sequencer_names,
        array_agg(DISTINCT seq.id) AS sequencer_ids
    FROM index_generator_pool_samples ps2
    JOIN index_generator_pool p2 ON ps2.pool_id = p2.id
    JOIN sequencer_lane lane2 ON lane2.pool_id = p2.id
    JOIN sequencer_flowcell_lanes fc_lane ON fc_lane.lane_id = lane2.id
    JOIN sequencer_flowcell fc ON fc_lane.flowcell_id = fc.id
    LEFT JOIN sequencer_sequencer seq ON fc.sequencer_id = seq.id
    WHERE ps2.sample_id = s.id
) fcids ON TRUE

ORDER BY s.id;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("library_sample_shared", "0014_alter_historicallibraryprotocol_name_and_more"),
        ("sample", "0011_alter_sample_measuring_unit_and_more"),
        ("request", "0009_historicalrequest"),
        ("flowcell", "0004_archived_feature"),
    ]

    operations = [
        migrations.RunSQL(
            sql=VIEW_SQL, reverse_sql="DROP VIEW IF EXISTS complete_sample_data;"
        ),
    ]
