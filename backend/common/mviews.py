import logging
import threading
from django.db import connections

logger = logging.getLogger("db")


def _execute_refresh(sql: str) -> None:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute(sql)
    except Exception as e:
        logger.exception("Failed to refresh materialized view: %s", e)


def refresh_complete_data_materialized_views(concurrently: bool = True) -> None:
    """Refresh both complete_*_data materialized views."""
    sql_library = (
        "REFRESH MATERIALIZED VIEW CONCURRENTLY complete_library_data_mv;"
        if concurrently
        else "REFRESH MATERIALIZED VIEW complete_library_data_mv;"
    )
    sql_sample = (
        "REFRESH MATERIALIZED VIEW CONCURRENTLY complete_sample_data_mv;"
        if concurrently
        else "REFRESH MATERIALIZED VIEW complete_sample_data_mv;"
    )

    _execute_refresh(sql_library)
    _execute_refresh(sql_sample)


def refresh_immediately_non_blocking(concurrently: bool = True) -> None:
    """Refresh MVs in background thread for immediate operations"""

    def _refresh():
        try:
            refresh_complete_data_materialized_views(concurrently=concurrently)
        except Exception as e:
            logger.error(f"Background MV refresh failed: {e}")

    thread = threading.Thread(target=_refresh, daemon=True)
    thread.start()


_batch_refresh_timer = None
_batch_refresh_lock = threading.Lock()


def refresh_batched(concurrently: bool = True, delay: int = 2) -> None:
    """Batch multiple rapid refreshes into a single operation"""
    global _batch_refresh_timer

    def _perform_refresh():
        global _batch_refresh_timer
        with _batch_refresh_lock:
            if _batch_refresh_timer:
                _batch_refresh_timer.cancel()
                _batch_refresh_timer = None
        refresh_complete_data_materialized_views(concurrently=concurrently)

    with _batch_refresh_lock:
        if _batch_refresh_timer:
            _batch_refresh_timer.cancel()

        _batch_refresh_timer = threading.Timer(delay, _perform_refresh)
        _batch_refresh_timer.daemon = True
        _batch_refresh_timer.start()
