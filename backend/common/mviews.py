import logging
import threading
from collections.abc import Iterable, Sequence

from django.db import connections, transaction, close_old_connections

from common.sql import (
    LIBRARY_CREATE_TABLE_SQL,
    LIBRARY_INDEX_SQL,
    SAMPLE_CREATE_TABLE_SQL,
    SAMPLE_INDEX_SQL,
    library_insert_sql_from_select,
    library_select_sql,
    sample_insert_sql_from_select,
    sample_select_sql,
)

logger = logging.getLogger("db")


def _split_sql_statements(sql: str) -> list[str]:
    return [
        f"{statement.strip()};"
        for statement in sql.strip().split(";")
        if statement.strip()
    ]


def _ensure_denormalized_tables_exist() -> None:
    statements = [
        LIBRARY_CREATE_TABLE_SQL,
        SAMPLE_CREATE_TABLE_SQL,
        *_split_sql_statements(LIBRARY_INDEX_SQL),
        *_split_sql_statements(SAMPLE_INDEX_SQL),
    ]

    with connections["default"].cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


_pending_library_ids: set[int] = set()
_pending_sample_ids: set[int] = set()
_pending_full_refresh = False
_batch_refresh_timer: threading.Timer | None = None
_batch_refresh_lock = threading.Lock()


def _make_iterable(values: Iterable[int] | None) -> Sequence[int]:
    if not values:
        return ()
    return tuple(sorted({int(v) for v in values if v is not None}))


def _execute_library_refresh(library_ids: Sequence[int]) -> None:
    if not library_ids:
        return

    where_clause = "WHERE l.id = ANY(%s)"
    select_clause = library_select_sql(where_clause=where_clause)
    sql = library_insert_sql_from_select(select_clause)

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
    select_clause = sample_select_sql(where_clause=where_clause)
    sql = sample_insert_sql_from_select(select_clause)

    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "DELETE FROM complete_sample_data_mv WHERE sample_id = ANY(%s)",
                [list(sample_ids)],
            )
            cursor.execute(sql, [list(sample_ids)])


def _execute_full_refresh() -> None:
    library_select = library_select_sql()
    sample_select = sample_select_sql()
    library_sql = library_insert_sql_from_select(library_select)
    sample_sql = sample_insert_sql_from_select(sample_select)

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

        if full_refresh or library_ids or sample_ids:
            _ensure_denormalized_tables_exist()

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
    library_ids: Iterable[int] | None = None,
    sample_ids: Iterable[int] | None = None,
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
    library_ids: Iterable[int] | None = None,
    sample_ids: Iterable[int] | None = None,
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
    library_ids: Iterable[int] | None = None,
    sample_ids: Iterable[int] | None = None,
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
    library_ids: Iterable[int] | None = None,
    sample_ids: Iterable[int] | None = None,
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
