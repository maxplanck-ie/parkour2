"""Backward-compatible alias module.

The LibraryType -> AnalysisType rename (library_sample_shared migration
0016) originally broke replaying production's real migration history from
an empty database: library.0009/0011 and sample.0011/0015 rebuild the
complete_library_data_mv / complete_sample_data_mv summary tables using
common.sql's library_insert_sql/library_create_mv_sql/sample_insert_sql/
sample_create_mv_sql, and those used to reflect the *current* (post-rename)
schema -- wrong for migrations that run before the rename.

That is now fixed at the source: common.sql's no-arg wrapper functions are
permanently pinned to the pre-rename JOIN (see the comment above their
definitions there), since nothing in the live app calls them -- only these
historical migrations do. This module just re-exports them, kept around so
any migration file still importing from here (rather than common.sql
directly) keeps working unchanged.
"""

from __future__ import annotations

from common.sql import (
    LIBRARY_CREATE_TABLE_SQL,
    LIBRARY_DROP_MV_SQL,
    LIBRARY_DROP_VIEW_SQL,
    LIBRARY_INDEX_SQL,
    SAMPLE_CREATE_TABLE_SQL,
    SAMPLE_DROP_MV_SQL,
    SAMPLE_INDEX_SQL,
    library_create_mv_sql,
    library_insert_sql,
    sample_create_mv_sql,
    sample_insert_sql,
)

__all__ = [
    "LIBRARY_CREATE_TABLE_SQL",
    "LIBRARY_DROP_MV_SQL",
    "LIBRARY_DROP_VIEW_SQL",
    "LIBRARY_INDEX_SQL",
    "SAMPLE_CREATE_TABLE_SQL",
    "SAMPLE_DROP_MV_SQL",
    "SAMPLE_INDEX_SQL",
    "library_create_mv_sql",
    "library_insert_sql",
    "sample_create_mv_sql",
    "sample_insert_sql",
]
