# Canada's wildfires, 2023 to 2026

Week 2 of The Median Canadian: an interactive page on Canada's four record fire seasons, built from raw public data.
Published with GitHub Pages at https://sjvadrevu.github.io/canada-wildfires-2026/

## What the site shows

- **The story, in nine parts:** how much burned against every year since 1972, the warming and the drought behind it, how far the fires went past what the usual drivers predict, smoke deaths against deaths in the fires, buildings and roads, the cost, and carbon, reburns and caribou.
- **Fire area map:** all 186 fire management areas, coloured by the share of forest burned compared with each area's own 1991 to 2020 average, for 2023, 2024, 2025, 2026 or 2023 to 2026. Tap an area for hectares, share burned, times its normal, whether it is a record, and its history since 1972. Layers: 2026 fire outlines, land that burned before, boreal caribou ranges, and BC drinking-water watersheds more than 10% burned.
- **Season replay:** weekly 2026 satellite fire detections for Canada or one province, with fire outlines appearing in the week they were first seen.
- **Find your city:** for 1,031 places, the nearest 2026 wildfire, smoky days from 2018 to 2026, the worst day, a 2026 daily smoke calendar, and the province's firefighting cost per resident where one is published. Real-time (not yet validated) air data is labelled.

## Files

| Path | What it is |
|---|---|
| `index.html` | The page (plain HTML, CSS and JavaScript; d3 7.9.0 and topojson-client 3.1.0 from jsDelivr) |
| `data/story.json` | Every number in the story and charts, keyed by claim ID (C1 to C40, plus C1b and X for derived counts) |
| `data/map/*.json` | Map geometry (TopoJSON, Canada Atlas Lambert, simplified) and per-area attributes |
| `data/cities.json`, `data/smoke2026.json` | Find-your-city table and the 2026 daily smoke calendar |
| `scripts/` | Build scripts that regenerate everything in `data/` |

## Rebuilding the data

The analysis folder (holding `analysis/` and `story/`) is passed with `--src` or the `WILDFIRE_SRC` environment variable. Claims come from `story/verified_numbers.json` when it exists, otherwise from the draft values in the script.

```
python scripts/build_story_json.py --src /path/to/wildfire
python scripts/fma_union.py /path/to/wildfire
MAPSHAPER=/path/to/mapshaper python scripts/build_map.py --src /path/to/wildfire
python scripts/build_cities.py --src /path/to/wildfire
```

`build_story_json.py` alone refreshes every number on the page.

## Sources

Natural Resources Canada, Canadian Forest Service (National Burned Area Composite, Canadian Wildland Fire Information System, National Forestry Database, Land Cover of Canada 2020, SCANFI, National Hydro Network); Canadian Interagency Forest Fire Centre and provincial and territorial fire agencies; Parks Canada; Environment and Climate Change Canada (climate station data, National Air Pollution Surveillance, National Inventory Report 2026, boreal caribou ranges); Agriculture and Agri-Food Canada (Canadian Drought Monitor); Statistics Canada (2021 Census, population centres, boundaries); Health Canada (AQBAT coefficients); US EPA AirNow; Transportation Safety Board; Public Safety Canada; Indigenous Services Canada; Copernicus Sentinel-2; Microsoft building footprints; Province of British Columbia; provincial public accounts. Every analysis is our own.

## Licence

Text, charts and images: CC BY 4.0 (see LICENSE-CONTENT.md). Code: MIT (see LICENSE).
Data belongs to its publishers; see LICENSE-CONTENT.md.

The Median Canadian. A curious Canadian explaining Canada through numbers, every week.
