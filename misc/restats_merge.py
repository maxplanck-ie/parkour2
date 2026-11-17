#!/usr/bin/env python3
"""Merge restats sqlite files: restats_merge.py OUT SRC1 [SRC2 ...]

First source wins on the UNIQUE key (flowcell_id, kind, key, field). Both the
`mismatches`, `matches`, `scanned` and `scan_runs` tables are merged (the last
three only if a source has them). An earlier source wins per key across both tables (a later match never replaces an earlier mismatch, and the reverse).
"""
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

out, *srcs = sys.argv[1:]
if not srcs:
    sys.exit(__doc__)
shutil.copy(srcs[0], out)
con = sqlite3.connect(out)
con.executescript(
    "CREATE TABLE IF NOT EXISTS matches (flowcell_id TEXT NOT NULL, kind TEXT NOT NULL,"
    " key TEXT NOT NULL, field TEXT NOT NULL, value REAL, run_date TEXT NOT NULL,"
    " UNIQUE (flowcell_id, kind, key, field))"
)
import restats  # noqa: E402  (schema of the optional tables)

for t in ("scanned", "scan_runs"):
    sql = next(x for x in restats.SCHEMA.split(";") if f"EXISTS {t} " in x)
    con.execute(sql)
cols = ", ".join(f'"{r[1]}"' for r in con.execute("PRAGMA table_info(mismatches)") if r[1] != "id")
count = lambda t, p="": con.execute(f"select count(*) from {p}{t}").fetchone()[0]
print(f"{srcs[0]}: {count('mismatches')} mismatches, {count('matches')} matches")
for i, s in enumerate(srcs[1:]):
    con.execute(f"ATTACH DATABASE ? AS o{i}", (s,))
    m0, k0 = count("mismatches"), count("matches")
    # an earlier source wins per key across BOTH tables
    seen = "{t}.flowcell_id=x.flowcell_id AND {t}.kind=x.kind AND {t}.key=x.key AND {t}.field=x.field"
    con.execute(
        f"INSERT OR IGNORE INTO mismatches ({cols}) SELECT {cols} FROM o{i}.mismatches x"
        f" WHERE NOT EXISTS (SELECT 1 FROM matches WHERE {seen.format(t='matches')})"
    )
    if con.execute(f"SELECT 1 FROM o{i}.sqlite_master WHERE name='matches'").fetchone():
        con.execute(
            f"INSERT OR IGNORE INTO matches SELECT * FROM o{i}.matches x"
            f" WHERE NOT EXISTS (SELECT 1 FROM mismatches WHERE {seen.format(t='mismatches')})"
        )
    for t in ("scanned", "scan_runs"):
        if con.execute(f"SELECT 1 FROM o{i}.sqlite_master WHERE name='{t}'").fetchone():
            con.execute(f"INSERT OR IGNORE INTO {t} SELECT * FROM o{i}.{t}")
    print(f"{s}: +{count('mismatches') - m0} mismatches, +{count('matches') - k0} matches")
con.commit()
print(f"{out}: {count('mismatches')} mismatches, {count('matches')} matches, {count('scanned')} scanned dirs")
