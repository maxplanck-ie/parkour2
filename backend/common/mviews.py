import logging
import threading
from typing import Iterable, Optional, Sequence, Set

from django.db import connections, transaction, close_old_connections

logger = logging.getLogger("db")


LIBRARY_SELECT_SQL = """
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
"""


SAMPLE_SELECT_SQL = """
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
"""


LIBRARY_INSERT_SQL = f"""
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
{{select_clause}}
"""

SAMPLE_INSERT_SQL = f"""
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
{{select_clause}}
"""


_pending_library_ids: Set[int] = set()
_pending_sample_ids: Set[int] = set()
_pending_full_refresh = False
_batch_refresh_timer: Optional[threading.Timer] = None
_batch_refresh_lock = threading.Lock()


def _make_iterable(values: Optional[Iterable[int]]) -> Sequence[int]:
    if not values:
        return ()
    return tuple(sorted(set(int(v) for v in values if v is not None)))


def _execute_library_refresh(library_ids: Sequence[int]) -> None:
    if not library_ids:
        return

    where_clause = "WHERE l.id = ANY(%s)"
    select_clause = LIBRARY_SELECT_SQL.format(where_clause=where_clause)
    sql = LIBRARY_INSERT_SQL.format(select_clause=select_clause)

    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "DELETE FROM complete_library_data_mv WHERE library_id = ANY(%s)",
                [list(library_ids)],
            )
            cursor.execute(sql, [list(library_ids)])


def _execute_sample_refresh(sample_ids: Sequence[int]) -> None:
    if not sample_ids:
        return

    where_clause = "WHERE s.id = ANY(%s)"
    select_clause = SAMPLE_SELECT_SQL.format(where_clause=where_clause)
    sql = SAMPLE_INSERT_SQL.format(select_clause=select_clause)

    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "DELETE FROM complete_sample_data_mv WHERE sample_id = ANY(%s)",
                [list(sample_ids)],
            )
            cursor.execute(sql, [list(sample_ids)])


def _execute_full_refresh() -> None:
    library_select = LIBRARY_SELECT_SQL.format(where_clause="")
    sample_select = SAMPLE_SELECT_SQL.format(where_clause="")
    library_sql = LIBRARY_INSERT_SQL.format(select_clause=library_select)
    sample_sql = SAMPLE_INSERT_SQL.format(select_clause=sample_select)

    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute("TRUNCATE TABLE complete_library_data_mv;")
            cursor.execute("TRUNCATE TABLE complete_sample_data_mv;")
            cursor.execute(library_sql)
            cursor.execute(sample_sql)


def _drain_and_refresh() -> None:
    global _pending_full_refresh, _batch_refresh_timer
    close_old_connections()
    try:
        with _batch_refresh_lock:
            library_ids = _make_iterable(_pending_library_ids)
            sample_ids = _make_iterable(_pending_sample_ids)
            full_refresh = _pending_full_refresh
            _pending_library_ids.clear()
            _pending_sample_ids.clear()
            _pending_full_refresh = False
            if _batch_refresh_timer:
                _batch_refresh_timer.cancel()
            _batch_refresh_timer = None

        if full_refresh:
            logger.debug("Executing full denormalized data refresh")
            _execute_full_refresh()
            return

        if library_ids:
            logger.debug(
                "Refreshing denormalized library data for IDs: %s", library_ids
            )
            _execute_library_refresh(library_ids)

        if sample_ids:
            logger.debug("Refreshing denormalized sample data for IDs: %s", sample_ids)
            _execute_sample_refresh(sample_ids)
    except Exception:
        logger.exception("Failed to refresh denormalized complete data tables")
    finally:
        close_old_connections()


def _schedule_refresh(delay: float) -> None:
    global _batch_refresh_timer
    timer = threading.Timer(delay, _drain_and_refresh)
    timer.daemon = True
    _batch_refresh_timer = timer
    timer.start()


def _queue_refresh(
    library_ids: Optional[Iterable[int]] = None,
    sample_ids: Optional[Iterable[int]] = None,
    full_refresh: bool = False,
    delay: float = 0.0,
) -> None:
    global _pending_full_refresh, _batch_refresh_timer

    libraries = set(library_ids or [])
    samples = set(sample_ids or [])

    with _batch_refresh_lock:
        if full_refresh:
            _pending_full_refresh = True
            _pending_library_ids.clear()
            _pending_sample_ids.clear()
        if not _pending_full_refresh:
            _pending_library_ids.update(libraries)
            _pending_sample_ids.update(samples)

        if _batch_refresh_timer:
            _batch_refresh_timer.cancel()
            _batch_refresh_timer = None

        _schedule_refresh(delay)


def refresh_complete_data_materialized_views(
    concurrently: bool = True,
    library_ids: Optional[Iterable[int]] = None,
    sample_ids: Optional[Iterable[int]] = None,
    full_refresh: bool = False,
) -> None:
    """
    Refresh the denormalized complete_*_data tables.

    The concurrently flag is retained for backwards-compatibility and ignored.
    """
    if not full_refresh and not library_ids and not sample_ids:
        full_refresh = True

    _queue_refresh(
        library_ids=library_ids,
        sample_ids=sample_ids,
        full_refresh=full_refresh,
        delay=0.0,
    )


def refresh_immediately_non_blocking(
    concurrently: bool = True,
    library_ids: Optional[Iterable[int]] = None,
    sample_ids: Optional[Iterable[int]] = None,
    full_refresh: bool = False,
) -> None:
    """Queue a refresh in the background as soon as possible."""
    refresh_complete_data_materialized_views(
        concurrently=concurrently,
        library_ids=library_ids,
        sample_ids=sample_ids,
        full_refresh=full_refresh,
    )


def refresh_batched(
    concurrently: bool = True,
    delay: float = 2.0,
    library_ids: Optional[Iterable[int]] = None,
    sample_ids: Optional[Iterable[int]] = None,
    full_refresh: bool = False,
) -> None:
    """
    Batch multiple rapid refreshes into a single operation.

    Subsequent calls received before the timer fires are coalesced.
    """
    if not full_refresh and not library_ids and not sample_ids:
        full_refresh = True

    _queue_refresh(
        library_ids=library_ids,
        sample_ids=sample_ids,
        full_refresh=full_refresh,
        delay=delay,
    )
