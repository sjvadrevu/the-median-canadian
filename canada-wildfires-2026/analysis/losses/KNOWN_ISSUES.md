# Known issues: losses

## TSB deaths (claim C19)
The first run of `scripts/03_tsb.py` summed the TSB INJURIES table, which repeats person rows. That double-counted
2024 (2 instead of 1) and 2026 (6 instead of 3). The independent verification (methods/verification.md, C19)
recounted from TSB's occurrence-level totals: 2023 1, 2024 1, 2025 2, 2026 3. The published numbers use the
corrected counts.

The script is fixed to use the occurrence-level totals, but `tsb_firefighting_by_year.csv` and
`human_cost_2023_2026.csv` in this folder are still the first-run outputs, because the TSB files could not be
downloaded again when the fix was made. Rerun `scripts/03_tsb.py` after `scripts/download_data.sh` to regenerate them.

## Deaths at CFB Wainwright
The 2026 count of deaths in the fires on the page and slides adds 4 Canadian Armed Forces members who died in the
CFB Wainwright fire on October 17, 2026 (Department of National Defence release, October 18, 2026). This is not in
the TSB data, which covers aviation only.
