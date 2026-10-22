"""Shared paths and settings for the climate-chain analysis (analysis/climate/).

Area file: set AREA_FILE to a GeoPackage with the columns of data/geo/fma_all.gpkg (fma_id integer,
agency, area_name, province, area_level). Rows whose agency is "Parks Canada" are an overlapping layer
and are ignored; the remaining rows must tile Canada. Area-dependent outputs are cached under
work/areas_<hash>/ so a new area file triggers a rebuild of the area steps (03 onward) only; the
downloads and station/year metrics (01, 02, 04) do not depend on the areas.
"""
import hashlib
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                       # analysis/climate
BASE = OUT.parents[1]                   # .../wildfire
RAW = OUT / "raw"
WORK = OUT / "work"
WORK.mkdir(exist_ok=True)
FOREST = BASE / "analysis" / "forest"
FOREST_WORK = FOREST / "work"
DEFAULT_AREA_FILE = BASE / "data" / "geo" / "fma_all.gpkg"
AREA_FILE = Path(os.environ.get("AREA_FILE", str(DEFAULT_AREA_FILE))).resolve()

YEARS = list(range(1991, 2027))         # fire years in the panel
NORMAL = (1991, 2020)
THREAD_KM = float(os.environ.get("THREAD_KM", 5))
THREAD_DZ = 100.0                       # max elevation difference (m) for joining station IDs

# region used for the regional breakdown
REGION = {"BC": "BC", "AB": "Prairies", "SK": "Prairies", "MB": "Prairies", "ON": "Ontario",
          "QC": "Quebec", "YT": "North", "NT": "North", "NU": "North",
          "NB": "Atlantic", "NS": "Atlantic", "PE": "Atlantic", "NL": "Atlantic"}


def area_hash():
    h = hashlib.sha1()
    with open(AREA_FILE, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def area_dir():
    d = WORK / f"areas_{area_hash()}"
    d.mkdir(exist_ok=True)
    return d


def log(msg, fh=None):
    print(msg, flush=True)
    if fh is not None:
        fh.write(str(msg) + "\n")
        fh.flush()


def out_dir():
    """Where area-dependent results go: analysis/climate/ for the default area file, otherwise
    work/areas_<hash>/ so the main panel is not overwritten by a trial area layer."""
    return OUT if AREA_FILE == DEFAULT_AREA_FILE.resolve() else area_dir()
