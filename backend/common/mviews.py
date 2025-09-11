import logging
import threading
from django.db import connections, transaction


def _execute_refresh(sql: str) -> None:
    logger = logging.getLogger("db")
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute(sql)
    except Exception as e:
        logger.exception("Failed to refresh materialized view: %s", e)


def refresh_library_mv(concurrently: bool = True) -> None:
    sql = (
        "REFRESH MATERIALIZED VIEW CONCURRENTLY complete_library_data_mv;"
        if concurrently
        else "REFRESH MATERIALIZED VIEW complete_library_data_mv;"
    )
    _execute_refresh(sql)


def refresh_sample_mv(concurrently: bool = True) -> None:
    sql = (
        "REFRESH MATERIALIZED VIEW CONCURRENTLY complete_sample_data_mv;"
        if concurrently
        else "REFRESH MATERIALIZED VIEW complete_sample_data_mv;"
    )
    _execute_refresh(sql)


def refresh_complete_data_materialized_views(concurrently: bool = True) -> None:
    """Refresh both complete_*_data materialized views.

    Uses CONCURRENTLY by default to avoid blocking reads. Assumes a unique
    index exists on the MV (created in migrations). Should be run outside of
    an atomic transaction; when called from model signals, wrap in
    transaction.on_commit to run after the outer transaction completes.
    """
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

    # Use a fresh cursor on default connection
    _execute_refresh(sql_library)
    _execute_refresh(sql_sample)


# Non-blocking schedulers (run after commit in a background thread)
def schedule_refresh_library_mv(concurrently: bool = True) -> None:
    # Offload to a background thread after commit to keep writes fast
    def _run():
        refresh_library_mv(concurrently=concurrently)

    transaction.on_commit(lambda: threading.Thread(target=_run, daemon=True).start())


def schedule_refresh_sample_mv(concurrently: bool = True) -> None:
    # Offload to a background thread after commit to keep writes fast
    def _run():
        refresh_sample_mv(concurrently=concurrently)

    transaction.on_commit(lambda: threading.Thread(target=_run, daemon=True).start())


def schedule_refresh_complete_data_materialized_views(
    concurrently: bool = True,
) -> None:
    # Offload to a background thread after commit to keep writes fast
    def _run():
        refresh_complete_data_materialized_views(concurrently=concurrently)

    transaction.on_commit(lambda: threading.Thread(target=_run, daemon=True).start())
