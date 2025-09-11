from django.db import migrations


CREATE_SQL = """
CREATE MATERIALIZED VIEW complete_library_data_mv AS
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
    l.read_length_id,
    l.index_i7,
    l.index_i5,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    it.name AS index_type_name,
    COALESCE(i7.prefix, '') || COALESCE(i7.number, '') AS i7_id,
    COALESCE(i5.prefix, '') || COALESCE(i5.number, '') AS i5_id,
    CASE
        WHEN ip.char_coord IS NOT NULL AND ip.num_coord IS NOT NULL
        THEN ip.char_coord || ip.num_coord::text
        ELSE ''
    END AS coordinate,
    rl.name AS read_length_name,
    pools.pool_names,
    fcids.flowcell_ids,
    fcids.sequencer_names,
    fcids.sequencer_ids,
    to_tsvector('simple',
        COALESCE(l.name,'') || ' ' ||
        COALESCE(l.barcode,'') || ' ' ||
        COALESCE(r.name,'') || ' ' ||
        COALESCE(array_to_string(pools.pool_names,' '),'') || ' ' ||
        COALESCE(array_to_string(fcids.flowcell_ids,' '),'')
    ) AS search_vector
FROM library_library AS l
JOIN request_request_libraries AS rrl ON l.id = rrl.library_id
JOIN request_request AS r ON rrl.request_id = r.id
LEFT JOIN library_sample_shared_libraryprotocol AS lp ON l.library_protocol_id = lp.id
LEFT JOIN library_sample_shared_librarytype AS lt ON l.library_type_id = lt.id
LEFT JOIN library_sample_shared_indextype AS it ON l.index_type_id = it.id
LEFT JOIN library_sample_shared_readlength AS rl ON l.read_length_id = rl.id
LEFT JOIN library_sample_shared_indexi7 AS i7 ON i7.index = l.index_i7
LEFT JOIN library_sample_shared_indexi5 AS i5 ON i5.index = l.index_i5
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT p.name) AS pool_names
    FROM index_generator_pool_libraries pl
    JOIN index_generator_pool p ON pl.pool_id = p.id
    WHERE pl.library_id = l.id
) pools ON TRUE
LEFT JOIN LATERAL (
    SELECT
        array_agg(DISTINCT fc.flowcell_id) AS flowcell_ids,
        array_agg(DISTINCT seq.name) AS sequencer_names,
        array_agg(DISTINCT seq.id::integer) AS sequencer_ids
    FROM index_generator_pool_libraries ipl2
    JOIN index_generator_pool p2 ON ipl2.pool_id = p2.id
    JOIN flowcell_lane lane2 ON lane2.pool_id = p2.id
    JOIN flowcell_flowcell_lanes fc_lane ON fc_lane.lane_id = lane2.id
    JOIN flowcell_flowcell fc ON fc_lane.flowcell_id = fc.id
    LEFT JOIN flowcell_sequencer seq ON fc.sequencer_id = seq.id
    WHERE ipl2.library_id = l.id
) fcids ON TRUE;
"""


INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_cld_mv_pk ON complete_library_data_mv (library_id, request_id);
CREATE INDEX IF NOT EXISTS idx_cld_mv_create_time ON complete_library_data_mv (create_time DESC);
CREATE INDEX IF NOT EXISTS idx_cld_mv_request_id ON complete_library_data_mv (request_id);
CREATE INDEX IF NOT EXISTS idx_cld_mv_request_name ON complete_library_data_mv (request_name);
CREATE INDEX IF NOT EXISTS idx_cld_mv_status ON complete_library_data_mv (status);
CREATE INDEX IF NOT EXISTS idx_cld_mv_library_protocol_id ON complete_library_data_mv (library_protocol_id);
CREATE INDEX IF NOT EXISTS idx_cld_mv_analysis_type_id ON complete_library_data_mv (analysis_type_id);
CREATE INDEX IF NOT EXISTS idx_cld_mv_read_length_id ON complete_library_data_mv (read_length_id);
CREATE INDEX IF NOT EXISTS idx_cld_mv_sequencer_ids ON complete_library_data_mv USING GIN (sequencer_ids);
CREATE INDEX IF NOT EXISTS idx_cld_mv_flowcell_ids ON complete_library_data_mv USING GIN (flowcell_ids);
CREATE INDEX IF NOT EXISTS idx_cld_mv_pool_names ON complete_library_data_mv USING GIN (pool_names);
CREATE INDEX IF NOT EXISTS idx_cld_mv_search_vector ON complete_library_data_mv USING GIN (search_vector);
"""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("library", "0009_completelibrarydata"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP MATERIALIZED VIEW IF EXISTS complete_library_data_mv;",
            reverse_sql="",
        ),
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql="DROP MATERIALIZED VIEW IF EXISTS complete_library_data_mv;"),
        migrations.RunSQL(sql="REFRESH MATERIALIZED VIEW complete_library_data_mv;", reverse_sql=""),
        migrations.RunSQL(sql=INDEX_SQL, reverse_sql=""),
    ]
