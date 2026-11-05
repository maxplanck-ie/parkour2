#!/usr/bin/env python3
"""Plot library concentration and duplication rate per protocol from Parkour.

Joins CompleteLibraryData (concentration_library in ng/µl, protocol name) to the
optical duplicate rate stored in each flowcell's sequences JSON, by barcode.

  - Ultra II: density (too many points for a rug to read)
  - UltraExpress: rug, since it has few rows with a concentration

Run inside the Parkour Django shell, which has the models loaded:

    docker exec -i parkour2-django python manage.py shell < misc/protocol_plots.py

Writes PNGs to /tmp/protocol_plots/. The shell passes no argv, so the output
directory is fixed.
"""

import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from flowcell.models import Flowcell
from library.models import CompleteLibraryData

PROTOCOLS = {
    "NEBNext UltraExpress DNA Library Prep Kit": "UltraExpress",
    "NEBNext Ultra II DNA Library Prep Kit for Illumina": "Ultra II",
}
OUT = "/tmp/protocol_plots"
os.makedirs(OUT, exist_ok=True)

# barcode -> optical_duplicates, across all flowcells
dupByBarcode = defaultdict(list)
for fc in Flowcell.objects.exclude(sequences=None).only("sequences"):
    for entry in fc.sequences:
        if entry.get("optical_duplicates") is not None:
            dupByBarcode[entry["barcode"]].append(entry["optical_duplicates"])

rows = defaultdict(lambda: {"conc": [], "dup": []})
for lib in CompleteLibraryData.objects.filter(
    library_protocol_name__in=PROTOCOLS.keys()
).only("barcode", "library_protocol_name", "concentration_library"):
    label = PROTOCOLS[lib.library_protocol_name]
    if lib.concentration_library is not None:
        rows[label]["conc"].append(lib.concentration_library)
    for d in dupByBarcode.get(lib.barcode, []):
        rows[label]["dup"].append(d)


def kde(values, xs):
    """Gaussian KDE with Silverman bandwidth, numpy only (no scipy in the container)."""
    n = len(values)
    h = 1.06 * values.std(ddof=1) * n ** (-1 / 5) or 1e-6
    z = (xs[:, None] - values[None, :]) / h
    return np.exp(-0.5 * z**2).sum(axis=1) / (n * h * np.sqrt(2 * np.pi))


def density(ax, values, title, xlabel):
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        ax.text(0.5, 0.5, f"n={len(values)}", ha="center", transform=ax.transAxes)
    else:
        xs = np.linspace(values.min(), values.max(), 200)
        ys = kde(values, xs)
        ax.plot(xs, ys)
        ax.fill_between(xs, ys, alpha=0.3)
    ax.set_title(f"{title} (n={len(values)})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("density")


def rug(ax, values, title, xlabel):
    values = np.asarray(values, dtype=float)
    ax.plot(values, np.zeros_like(values), "|", markersize=18, color="C1")
    ax.set_yticks([])
    ax.set_title(f"{title} (n={len(values)})")
    ax.set_xlabel(xlabel)


for label, kind in [("Ultra II", density), ("UltraExpress", rug)]:
    for metric, key, xlabel in [
        ("conc", "conc", "concentration_library (ng/µl)"),
        ("dup", "dup", "optical duplicates (%)"),
    ]:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        kind(ax, rows[label][key], f"{label} {metric}", xlabel)
        fig.tight_layout()
        path = f"{OUT}/{label.replace(' ', '_')}_{metric}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        print("wrote", path)
