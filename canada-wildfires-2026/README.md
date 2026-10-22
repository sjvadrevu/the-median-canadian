# Canada's wildfires, 2023 to 2026

Week 2 of The Median Canadian: an interactive page on Canada's four record fire seasons, built from raw public data.
Published with GitHub Pages at https://sjvadrevu.github.io/canada-wildfires-2026/

Everything behind the page is here: every analysis script, every output table, the independent check of every published number, and the steps to rebuild it from the official sources. Nothing is hidden, so anyone can reproduce or challenge any number.

- **[METHODOLOGY.md](METHODOLOGY.md):** what we measured and how, a table mapping every published claim (C1 to C40) to the script and file it comes from, and how to challenge a number.
- **[REPRODUCE.md](REPRODUCE.md):** environment, download, run order and runtimes.
- **[data/SOURCES.md](data/SOURCES.md):** every dataset with publisher, URL, licence, access date and use.
- **[methods/verification.md](methods/verification.md):** the independent verification of every claim.

## What the site shows

- **The story, in nine parts:** how much burned against every year since 1972, the warming and the drought behind it, how far the fires went past what the usual drivers predict, smoke deaths against deaths in the fires, buildings and roads, the cost, and carbon, reburns and caribou.
- **Fire area map:** all 186 fire management areas, coloured by the share of forest burned compared with each area's own 1991 to 2020 average, for 2023, 2024, 2025, 2026 or 2023 to 2026.
- **Season replay:** weekly 2026 satellite fire detections, with fire outlines appearing in the week they were first seen.
- **Find your city:** for 1,031 places, the nearest 2026 wildfire, smoky days from 2018 to 2026, and the province's firefighting cost per resident where one is published.

## Files

| Path | What it is |
|---|---|
| `index.html` | The page (plain HTML, CSS and JavaScript) |
| `data/story.json` | Every number in the story and charts, keyed by claim ID |
| `data/map/`, `data/cities.json`, `data/smoke2026.json` | Map geometry and attributes, city search table, 2026 smoke calendar |
| `analysis/<topic>/` | One folder per analysis: `scripts/`, `results.md` (findings and method), `manifest.csv` (sources), output CSVs |
| `analysis/REBUILD.md` | The 2026-10-21 rebuild onto the final area layer, with before and after values |
| `story/` | Draft claims and the verified values (`verified_numbers.json`) |
| `data/fire/`, `data/geo/`, `data/smoke-cost/` | Derived input tables, dated snapshots of official totals, build scripts and manifests |
| `season/` | Dated snapshots of official 2026 fire lists and NFD cause tables |
| `scripts/` | Page build scripts, data download (`download_data.py`), sources table (`build_sources.py`), analysis sync (`sync_analysis.py`) |
| `slides/` | Carousel builders |
| `methods/` | Verification and the list of files kept out of the repo because of size |

## Licence

- **Code:** Apache License 2.0 (see LICENSE and NOTICE).
- **Text, charts, maps and images:** CC BY 4.0 (see LICENSE-CONTENT.md).
- **Data:** belongs to its publishers and is used under their terms (data/SOURCES.md). Most federal data is under the Open Government Licence - Canada, Statistics Canada data under the Statistics Canada Open Licence. Building data derived from Microsoft Global ML Building Footprints (for example `analysis/losses/buildings_2026_near_outlines.gpkg` and the building counts) is under ODbL 1.0, as the source requires.

The Median Canadian. A curious Canadian explaining Canada through numbers, every week.
