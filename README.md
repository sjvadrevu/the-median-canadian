# The Median Canadian (moved)

The hub moved to https://mediancanadian.ca/ and its source to https://github.com/mediancanadian/mediancanadian.github.io. This repository only forwards the old address (sjvadrevu.github.io/the-median-canadian), which appears on posted slides.

# The Median Canadian

A curious Canadian explaining Canada through numbers, every week.

Site: https://sjvadrevu.github.io/the-median-canadian/ (the link in the Instagram bio)

Each week's story has its own repository, with its page, data, analysis code and full methodology, so anyone can check or challenge any number.

| Week | Story | Where |
|---|---|---|
| 2 | Talking trade with Türkiye, October 2026 | [canada-turkey-oct26](https://github.com/sjvadrevu/canada-turkey-oct26) |
| 1 | Alberta's separation vote, October 19, 2026 | [ab-referendum-live](https://github.com/sjvadrevu/ab-referendum-live) |

## The hub page

`index.html` is built by `hub/build_hub.py` from each week's own files: the cover slide in `covers/`, and the findings and numbers from the week's data, so the hub always matches the week's page. The build stops with a message if a finding listed on the hub no longer holds for the data.

To rebuild it:

1. Clone weeks 1 and 2 into this folder (git ignores them):
   `git clone https://github.com/sjvadrevu/ab-referendum-live ab-referendum-live`
   `git clone https://github.com/sjvadrevu/canada-turkey-oct26 canada-turkey-oct26`
2. `pip install pillow`
3. `python3 hub/build_hub.py`

Every week: its cover slide (the first image of the Instagram post) in `covers/` as `week-NN-cover.jpg`, and one entry in the `POSTS` list in `hub/build_hub.py` that reads its findings from the week's own files. The build stops if a week's folder has no entry or no cover.

## Licence

- **Code:** Apache License 2.0 (LICENSE and NOTICE).
- **Text, charts, maps and slides:** CC BY 4.0 (LICENSE-CONTENT.md).
- **Photo in the week 2 cover slide:** Anıtkabir, Ankara, by Nicoleon on Wikimedia Commons, CC0 1.0.
- **Data:** belongs to its publishers; each week's folder lists its sources and their licences.
