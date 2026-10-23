# The Median Canadian

A curious Canadian explaining Canada through numbers, every week.

Site: https://sjvadrevu.github.io/the-median-canadian/ (the link in the Instagram bio)

Each week's story lives in its own folder, with its page, data, analysis code and full methodology, so anyone can check or challenge any number.

| Week | Story | Where |
|---|---|---|
| 2 | Canada's wildfires, 2023 to 2026 | [canada-wildfires-2026/](canada-wildfires-2026/) |
| 1 | Alberta's separation vote, October 19, 2026 | [ab-referendum-live](https://github.com/sjvadrevu/ab-referendum-live), its own repository until the official results on October 29, 2026 |

## The hub page

`index.html` is built by `hub/build_hub.py` from each week's own files: the cover slide in `covers/`, and the findings and numbers from the week's data, so the hub always matches the week's page. The build stops with a message if a finding listed on the hub no longer holds for the data.

To rebuild it:

1. Clone week 1 into this folder (git ignores it until week 1 moves here):
   `git clone https://github.com/sjvadrevu/ab-referendum-live ab-referendum-live`
2. `pip install pillow`
3. `python3 hub/build_hub.py`

Every week: put its page in a new folder, its cover slide (the first image of the Instagram post) in `covers/` as `week-NN-cover.jpg`, and one entry in the `POSTS` list in `hub/build_hub.py`. The build stops if a week's folder has no entry or no cover.

## Licence

- **Code:** Apache License 2.0 (LICENSE and NOTICE).
- **Text, charts, maps and slides:** CC BY 4.0 (LICENSE-CONTENT.md).
- **Photos in the cover slides:** licensed from All Canada Photos and not covered by CC BY 4.0.
- **Data:** belongs to its publishers; each week's folder lists its sources and their licences.
