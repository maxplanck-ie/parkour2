from __future__ import annotations

from typing import Final


LIBRARY_DROP_VIEW_SQL: Final[str] = "DROP VIEW IF EXISTS complete_library_data;"
LIBRARY_DROP_MV_SQL: Final[str] = (
    "DROP MATERIALIZED VIEW IF EXISTS complete_library_data_mv CASCADE;"
)
SAMPLE_DROP_MV_SQL: Final[str] = (
    "DROP MATERIALIZED VIEW IF EXISTS complete_sample_data_mv CASCADE;"
)

LIBRARY_CREATE_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS complete_library_data_mv (
    library_id INTEGER PRIMARY KEY,
    barcode VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status INTEGER NOT NULL,
    sequencing_depth DOUBLE PRECISION,
    measuring_unit VARCHAR(50),
    measured_value DOUBLE PRECISION,
    concentration_library DOUBLE PRECISION,
    percent_total DOUBLE PRECISION,
    library_protocol_id INTEGER,
    library_protocol_name VARCHAR(150),
    analysis_type_id INTEGER,
    analysis_type_name VARCHAR(200),
    read_length_id INTEGER,
    read_length_name VARCHAR(50),
    average_fragment_size DOUBLE PRECISION,
    index_type_name VARCHAR(100),
    coordinate VARCHAR(3),
    index_i7 VARCHAR(24),
    i7_id VARCHAR(50),
    index_i5 VARCHAR(24),
    i5_id VARCHAR(50),
    request_id INTEGER,
    request_name VARCHAR(255),
    create_time TIMESTAMP WITH TIME ZONE,
    pool_names VARCHAR(100)[],
    flowcell_ids VARCHAR(50)[],
    sequencer_ids INTEGER[],
    sequencer_names VARCHAR(50)[],
    search_vector TSVECTOR
);
""".strip()

SAMPLE_CREATE_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS complete_sample_data_mv (
    sample_id INTEGER PRIMARY KEY,
    barcode VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status INTEGER NOT NULL,
    sequencing_depth DOUBLE PRECISION,
    nucleic_acid_type_id INTEGER,
    nucleic_acid_type_name VARCHAR(100),
    measuring_unit VARCHAR(50),
    measured_value DOUBLE PRECISION,
    concentration_library DOUBLE PRECISION,
    gmo BOOLEAN,
    library_protocol_id INTEGER,
    library_protocol_name VARCHAR(150),
    analysis_type_id INTEGER,
    analysis_type_name VARCHAR(200),
    read_length_id INTEGER,
    read_length_name VARCHAR(50),
    average_fragment_size DOUBLE PRECISION,
    starting_amount DOUBLE PRECISION,
    pcr_cycles INTEGER,
    index_type_name VARCHAR(100),
    coordinate VARCHAR(3),
    index_i7 VARCHAR(24),
    i7_id VARCHAR(50),
    index_i5 VARCHAR(24),
    i5_id VARCHAR(50),
    request_id INTEGER,
    request_name VARCHAR(255),
    create_time TIMESTAMP WITH TIME ZONE,
    pool_names VARCHAR(100)[],
    flowcell_ids VARCHAR(50)[],
    sequencer_ids INTEGER[],
    sequencer_names VARCHAR(50)[],
    search_vector TSVECTOR
);
""".strip()

LIBRARY_SELECT_SQL_TEMPLATE: Final[str] = """
SELECT DISTINCT ON (l.id, r.id)
    l.id AS library_id,
    l.barcode,
    l.name,
    l.status,
    l.sequencing_depth,
    l.measuring_unit,
    l.measured_value,
    l.measured_value_facility AS concentration_library,
    l.percent_total,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    l.read_length_id,
    rl.name AS read_length_name,
    l.size_distribution_facility AS average_fragment_size,
    it.name AS index_type_name,
    CASE
        WHEN ip.char_coord IS NOT NULL AND ip.num_coord IS NOT NULL
        THEN ip.char_coord || ip.num_coord::text
        ELSE ''
    END AS coordinate,
    l.index_i7,
    COALESCE(i7.prefix, '') || COALESCE(i7.number, '') AS i7_id,
    l.index_i5,
    COALESCE(i5.prefix, '') || COALESCE(i5.number, '') AS i5_id,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    pools.pool_names,
    fcids.flowcell_ids,
    fcids.sequencer_ids,
    fcids.sequencer_names,
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
LEFT JOIN library_sample_shared_indexi7 AS i7
    ON i7.index = l.index_i7
    AND EXISTS (
        SELECT 1
        FROM library_sample_shared_indextype_indices_i7 AS iti7
        WHERE iti7.indexi7_id = i7.id
          AND iti7.indextype_id = l.index_type_id
    )
LEFT JOIN library_sample_shared_indexi5 AS i5
    ON i5.index = l.index_i5
    AND EXISTS (
        SELECT 1
        FROM library_sample_shared_indextype_indices_i5 AS iti5
        WHERE iti5.indexi5_id = i5.id
          AND iti5.indextype_id = l.index_type_id
    )
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id AND ip.index_type_id = l.index_type_id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT p.name) AS pool_names
    FROM index_generator_pool_libraries pl
    JOIN index_generator_pool p ON pl.pool_id = p.id
    WHERE pl.library_id = l.id
) pools ON TRUE
LEFT JOIN LATERAL (
    SELECT
        array_agg(DISTINCT fc.flowcell_id) AS flowcell_ids,
        array_agg(DISTINCT seq.id::integer) AS sequencer_ids,
        array_agg(DISTINCT seq.name) AS sequencer_names
    FROM index_generator_pool_libraries ipl2
    JOIN index_generator_pool p2 ON ipl2.pool_id = p2.id
    JOIN flowcell_lane lane2 ON lane2.pool_id = p2.id
    JOIN flowcell_flowcell_lanes fc_lane ON fc_lane.lane_id = lane2.id
    JOIN flowcell_flowcell fc ON fc_lane.flowcell_id = fc.id
    LEFT JOIN flowcell_sequencer seq ON fc.sequencer_id = seq.id
    WHERE ipl2.library_id = l.id
) fcids ON TRUE
{where_clause}
ORDER BY l.id, r.id;
""".strip()

SAMPLE_SELECT_SQL_TEMPLATE: Final[str] = """
SELECT DISTINCT ON (s.id, r.id)
    s.id AS sample_id,
    s.barcode,
    s.name,
    s.status,
    s.sequencing_depth,
    nat.id AS nucleic_acid_type_id,
    nat.name AS nucleic_acid_type_name,
    s.measuring_unit,
    s.measured_value,
    lp2.concentration_library,
    s.gmo,
    lp.id AS library_protocol_id,
    lp.name AS library_protocol_name,
    lt.id AS analysis_type_id,
    lt.name AS analysis_type_name,
    s.read_length_id,
    rl.name AS read_length_name,
    lp2.mean_fragment_size AS average_fragment_size,
    lp2.starting_amount,
    lp2.pcr_cycles,
    it.name AS index_type_name,
    CASE
        WHEN ip.char_coord IS NOT NULL AND ip.num_coord IS NOT NULL
        THEN ip.char_coord || ip.num_coord::text
        ELSE ''
    END AS coordinate,
    s.index_i7,
    COALESCE(i7.prefix, '') || COALESCE(i7.number, '') AS i7_id,
    s.index_i5,
    COALESCE(i5.prefix, '') || COALESCE(i5.number, '') AS i5_id,
    r.id AS request_id,
    r.name AS request_name,
    r.create_time AS create_time,
    pools.pool_names,
    fcids.flowcell_ids,
    fcids.sequencer_ids,
    fcids.sequencer_names,
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
LEFT JOIN library_sample_shared_indexi7 AS i7
    ON i7.index = s.index_i7
    AND EXISTS (
        SELECT 1
        FROM library_sample_shared_indextype_indices_i7 AS iti7
        WHERE iti7.indexi7_id = i7.id
          AND iti7.indextype_id = s.index_type_id
    )
LEFT JOIN library_sample_shared_indexi5 AS i5
    ON i5.index = s.index_i5
    AND EXISTS (
        SELECT 1
        FROM library_sample_shared_indextype_indices_i5 AS iti5
        WHERE iti5.indexi5_id = i5.id
          AND iti5.indextype_id = s.index_type_id
    )
LEFT JOIN library_sample_shared_indexpair AS ip
    ON ip.index1_id = i7.id AND ip.index2_id = i5.id AND ip.index_type_id = s.index_type_id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT p.name) AS pool_names
    FROM index_generator_pool_samples ps
    JOIN index_generator_pool p ON ps.pool_id = p.id
    WHERE ps.sample_id = s.id
) pools ON TRUE
LEFT JOIN LATERAL (
    SELECT
        array_agg(DISTINCT fc.flowcell_id) AS flowcell_ids,
        array_agg(DISTINCT seq.id::integer) AS sequencer_ids,
        array_agg(DISTINCT seq.name) AS sequencer_names
    FROM index_generator_pool_samples ps2
    JOIN index_generator_pool p2 ON ps2.pool_id = p2.id
    JOIN flowcell_lane lane2 ON lane2.pool_id = p2.id
    JOIN flowcell_flowcell_lanes fc_lane ON fc_lane.lane_id = lane2.id
    JOIN flowcell_flowcell fc ON fc_lane.flowcell_id = fc.id
    LEFT JOIN flowcell_sequencer seq ON fc.sequencer_id = seq.id
    WHERE ps2.sample_id = s.id
) fcids ON TRUE
{where_clause}
ORDER BY s.id, r.id;
""".strip()

LIBRARY_INSERT_SQL_TEMPLATE: Final[str] = """
INSERT INTO complete_library_data_mv (
    library_id,
    barcode,
    name,
    status,
    sequencing_depth,
    measuring_unit,
    measured_value,
    concentration_library,
    percent_total,
    library_protocol_id,
    library_protocol_name,
    analysis_type_id,
    analysis_type_name,
    read_length_id,
    read_length_name,
    average_fragment_size,
    index_type_name,
    coordinate,
    index_i7,
    i7_id,
    index_i5,
    i5_id,
    request_id,
    request_name,
    create_time,
    pool_names,
    flowcell_ids,
    sequencer_ids,
    sequencer_names,
    search_vector
)
{select_clause}
""".strip()

SAMPLE_INSERT_SQL_TEMPLATE: Final[str] = """
INSERT INTO complete_sample_data_mv (
    sample_id,
    barcode,
    name,
    status,
    sequencing_depth,
    nucleic_acid_type_id,
    nucleic_acid_type_name,
    measuring_unit,
    measured_value,
    concentration_library,
    gmo,
    library_protocol_id,
    library_protocol_name,
    analysis_type_id,
    analysis_type_name,
    read_length_id,
    read_length_name,
    average_fragment_size,
    starting_amount,
    pcr_cycles,
    index_type_name,
    coordinate,
    index_i7,
    i7_id,
    index_i5,
    i5_id,
    request_id,
    request_name,
    create_time,
    pool_names,
    flowcell_ids,
    sequencer_ids,
    sequencer_names,
    search_vector
)
{select_clause}
""".strip()

LIBRARY_INDEX_SQL: Final[str] = """
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
""".strip()

SAMPLE_INDEX_SQL: Final[str] = """
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
""".strip()


def library_select_sql(where_clause: str = "") -> str:
    return LIBRARY_SELECT_SQL_TEMPLATE.format(where_clause=where_clause)


def sample_select_sql(where_clause: str = "") -> str:
    return SAMPLE_SELECT_SQL_TEMPLATE.format(where_clause=where_clause)


def library_insert_sql_from_select(select_clause: str) -> str:
    return LIBRARY_INSERT_SQL_TEMPLATE.format(select_clause=select_clause)


def sample_insert_sql_from_select(select_clause: str) -> str:
    return SAMPLE_INSERT_SQL_TEMPLATE.format(select_clause=select_clause)


def library_insert_sql(where_clause: str = "") -> str:
    return library_insert_sql_from_select(library_select_sql(where_clause))


def sample_insert_sql(where_clause: str = "") -> str:
    return sample_insert_sql_from_select(sample_select_sql(where_clause))


def library_create_mv_sql(where_clause: str = "") -> str:
    select_sql = library_select_sql(where_clause).strip()
    return f"""
CREATE MATERIALIZED VIEW complete_library_data_mv AS
{select_sql}
""".strip()


def sample_create_mv_sql(where_clause: str = "") -> str:
    select_sql = sample_select_sql(where_clause).strip()
    return f"""
CREATE MATERIALIZED VIEW complete_sample_data_mv AS
{select_sql}
""".strip()
