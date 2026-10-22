"""Merge per-cell check-event features (run_checks4.sh: work/features_<event>c<k>.csv, one 05_event_features.py run per
20 km footprint cell, each with its own offset) into work/features_<event>.csv and work/scenes_<event>.csv.
Per-cell dNBR rasters (work/dnbr_<event>c<k>.tif) and cell footprint files are regenerable and are deleted.
usage: 05c_merge_cells.py <event> [...]"""
import glob, os, sys
import pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); Wk = os.path.join(P, "work")
for ev in sys.argv[1:]:
    fs = sorted(glob.glob(os.path.join(Wk, f"features_{ev}c*.csv")))
    cells = sorted(glob.glob(os.path.join(Wk, f"fp_{ev}c*.csv.gz")))
    n_fp = sum(len(pd.read_csv(f)) for f in cells)
    d = pd.concat([pd.read_csv(f).assign(cell=os.path.basename(f)[len(f"features_{ev}"):-4]) for f in fs], ignore_index=True)
    assert len(fs) == len(cells) and len(d) == n_fp, (len(fs), len(cells), len(d), n_fp)
    d["event"] = ev
    d.to_csv(os.path.join(Wk, f"features_{ev}.csv"), index=False)
    sc = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(Wk, f"scenes_{ev}c*.csv")))], ignore_index=True)
    sc.to_csv(os.path.join(Wk, f"scenes_{ev}.csv"), index=False)
    print(ev, len(fs), "cells", len(d), "footprints; offsets", d.groupby("cell").dnbr_offset.first().round(1).to_dict())
    for f in fs + cells + glob.glob(os.path.join(Wk, f"dnbr_{ev}c*.tif")) + glob.glob(os.path.join(Wk, f"scenes_{ev}c*.csv")):
        os.remove(f)
