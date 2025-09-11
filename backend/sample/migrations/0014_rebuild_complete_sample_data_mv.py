from django.db import migrations


CREATE_SQL = """
CREATE MATERIALIZED VIEW complete_sample_data_mv AS
SELECT
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
    COALESCE(i7.prefix, '') || COALESCE(i7.number, '') AS i7_id,
    COALESCE(i5.prefix, '') || COALESCE(i5.number, '') AS i5_id,
    CASE
        WHEN ip.char_coord IS NOT NULL AND ip.num_coord IS NOT NULL
        THEN ip.char_coord || ip.num_coord::text
        ELSE ''
    END AS coordinate,
    it.name AS index_type_name,
    rl.name AS read_length_name,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    pools.pool_names,
    fcids.flowcell_ids,
    fcids.sequencer_names,
    fcids.sequencer_ids,
    to_tsvector('simple',
        COALESCE(s.name,'') || ' ' ||
        COALESCE(s.barcode,'') || ' ' ||
        COALESCE(r.name,'') || ' ' ||
        COALESCE(array_to_string(pools.pool_names,' '),'') || ' ' ||
        COALESCE(array_to_string(fcids.flowcell_ids,' '),'')
    ) AS search_vector
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
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT p.name) AS pool_names
    FROM index_generator_pool_samples ps
    JOIN index_generator_pool p ON ps.pool_id = p.id
    WHERE ps.sample_id = s.id
) pools ON TRUE
LEFT JOIN LATERAL (
    SELECT
        array_agg(DISTINCT fc.flowcell_id) AS flowcell_ids,
        array_agg(DISTINCT seq.name) AS sequencer_names,
        array_agg(DISTINCT seq.id::integer) AS sequencer_ids
    FROM index_generator_pool_samples ps2
    JOIN index_generator_pool p2 ON ps2.pool_id = p2.id
    JOIN flowcell_lane lane2 ON lane2.pool_id = p2.id
    JOIN flowcell_flowcell_lanes fc_lane ON fc_lane.lane_id = lane2.id
    JOIN flowcell_flowcell fc ON fc_lane.flowcell_id = fc.id
    LEFT JOIN flowcell_sequencer seq ON fc.sequencer_id = seq.id
    WHERE ps2.sample_id = s.id
) fcids ON TRUE;
"""


INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_csd_mv_pk ON complete_sample_data_mv (sample_id, request_id);
CREATE INDEX IF NOT EXISTS idx_csd_mv_create_time ON complete_sample_data_mv (create_time DESC);
CREATE INDEX IF NOT EXISTS idx_csd_mv_request_id ON complete_sample_data_mv (request_id);
CREATE INDEX IF NOT EXISTS idx_csd_mv_request_name ON complete_sample_data_mv (request_name);
CREATE INDEX IF NOT EXISTS idx_csd_mv_status ON complete_sample_data_mv (status);
CREATE INDEX IF NOT EXISTS idx_csd_mv_library_protocol_id ON complete_sample_data_mv (library_protocol_id);
CREATE INDEX IF NOT EXISTS idx_csd_mv_analysis_type_id ON complete_sample_data_mv (analysis_type_id);
CREATE INDEX IF NOT EXISTS idx_csd_mv_read_length_id ON complete_sample_data_mv (read_length_id);
CREATE INDEX IF NOT EXISTS idx_csd_mv_sequencer_ids ON complete_sample_data_mv USING GIN (sequencer_ids);
CREATE INDEX IF NOT EXISTS idx_csd_mv_flowcell_ids ON complete_sample_data_mv USING GIN (flowcell_ids);
CREATE INDEX IF NOT EXISTS idx_csd_mv_pool_names ON complete_sample_data_mv USING GIN (pool_names);
CREATE INDEX IF NOT EXISTS idx_csd_mv_search_vector ON complete_sample_data_mv USING GIN (search_vector);
"""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("sample", "0013_completesampledata"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP MATERIALIZED VIEW IF EXISTS complete_sample_data_mv;",
            reverse_sql="",
        ),
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql="DROP MATERIALIZED VIEW IF EXISTS complete_sample_data_mv;"),
        migrations.RunSQL(sql="REFRESH MATERIALIZED VIEW complete_sample_data_mv;", reverse_sql=""),
        migrations.RunSQL(sql=INDEX_SQL, reverse_sql=""),
    ]
