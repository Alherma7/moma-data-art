# Mondrian Chart — Real-Geometry Design

Date: 2026-08-06

Scope: the Mondrian chart only, as a pilot for a new technique. Demoiselles
and Dance I are untouched for now; they get their own design later.

## Concept

The painting's own rectangles are the data container. Instead of choosing
a chart type and coloring it to evoke a painting, the reference image's
actual rectangles are digitized and rendered as-is — same shapes, same
painted colors — so the chart looks exactly like the painting. Real MoMA
acquisition data is attached to those exact rectangles and revealed on
hover.

## Source image

`images/mondrian_composition.jpg`, already in the repo. Documented as a
composition representative of Mondrian's style — a grid of black lines
with red/blue/yellow/black blocks — without attributing it to a specific
catalogued work.

## Geometry digitization

Manual digitization: the image is inspected visually and each colored cell
is transcribed as one entry in a new module, `src/mondrian_geometry.py`:

```python
MONDRIAN_RECTANGLES = [
    {"x0": 0.02, "y0": 0.68, "x1": 0.10, "y1": 0.82, "color": "yellow"},
    {"x0": 0.10, "y0": 0.62, "x1": 0.22, "y1": 0.82, "color": "red"},
    # ... one entry per colored cell
]
```

- Coordinates are normalized to [0, 1] (fraction of image width/height);
  `color` is a key into `config.PALETTES["mondrian"]`.
- Only **colored** cells (red/blue/yellow/black) are digitized. White
  background cells stay decorative negative space, exactly as they
  function in the source composition, and carry no data.
- This is a one-time manual transcription rather than automated
  color-segmentation extraction: the geometry never changes, so a small
  hand-authored table is simpler than a new image-processing dependency
  dealing with JPEG artifacts and anti-aliased edges for a task done once.

## Data mapping

`Decade_acquired` (from `clean_artworks()`) is the data dimension.
Geometry stays fixed — assignment is rank-based, not size-based:

1. Count artworks per `Decade_acquired`, descending.
2. Sort the digitized rectangles by area, descending.
3. If there are more decades than colored rectangles: pool the smallest
   decades into a single `"Other"` bucket first, so the number of groups
   matches the number of rectangles.
4. If there are more rectangles than decades (after step 3): the smallest
   leftover rectangles get no data — painted color only, no hover content.
5. Zip sorted decades to sorted rectangles: rectangle rank *i* gets decade
   rank *i*. The largest rectangle is always the most-acquired decade.

Rectangles keep their **painted color** regardless of which decade lands
on them — color is not a data encoding, only the decade/count shown on
hover is. This is what keeps the chart looking like the actual painting
rather than a treemap wearing its palette.

## Rendering (`src/charts.py`)

`mondrian_treemap(df)`: one `go.Scatter` trace per digitized rectangle
(`fill='toself'`, exact painted color, `palette["black"]` border to echo
the grid lines), built from `MONDRIAN_RECTANGLES` coordinates. No background image — the
rectangles are drawn as flat vector shapes so edges stay crisp. Each
trace's `hovertemplate` shows the assigned decade and artwork count;
rectangles with no assigned decade get minimal/empty hover.

## Config

No per-painting image-path config is needed — `mondrian_treemap` is pure
vector (no background image). `demoiselles_voronoi`/`dance_scatter` and
their supporting code (`src/voronoi_treemap.py`, the old
`GEOMETRIZE_CONFIGS` dict, the `demoiselles`/`dance` palette entries) were
removed entirely rather than kept or renamed — they served only the two
charts being deferred to a future redesign, and were unused dead weight
otherwise.

## Cleanup

`Credit_category` (`_CREDIT_CATEGORIES`, `classify_credit()` in
`src/data.py`, and the column in `clean_artworks()`) is removed — nothing
in the codebase uses it once `mondrian_treemap` no longer groups by it.
Its dedicated test in `tests/test_data.py`
(`test_classify_credit_matches_known_keywords`) and the `Credit_category`
fixture/assertions in the `clean_artworks` tests are removed with it.

## Development workflow

Notebook-first, not direct-to-`src/` TDD: the geometry, the assignment
logic, and the final render are each built and checked interactively in
`notebooks/03_mondrian_prototyping.ipynb` — the user runs every cell
themselves and confirms it before the next piece is built. Only once all
three are validated does the code move into `src/mondrian_geometry.py`
and `src/charts.py`, gaining proper pytest tests at that point.
`notebooks/02_chart_prototyping.ipynb` is the final check afterward,
exercising the graduated `charts.mondrian_treemap` against the real
dataset one more time.

## Validation and testing

- **Visual gate first**: before the assignment logic or real data is
  introduced, `MONDRIAN_RECTANGLES` is rendered standalone (painted
  colors only, no hover data) in `notebooks/03_mondrian_prototyping.ipynb`.
  The user runs this cell and confirms it reads as the source image
  before anything else is built on top of it.
- `tests/test_mondrian_geometry.py` (new, written at graduation time):
  every entry in `MONDRIAN_RECTANGLES` has `0 <= x0 < x1 <= 1`,
  `0 <= y0 < y1 <= 1`, and a `color` that exists in
  `config.PALETTES["mondrian"]`.
- `tests/test_charts.py` (new, written at graduation time): the
  rank-based assignment logic — given a small known set of decade counts
  and a small known set of rectangle areas, asserts the correct decade
  lands on each rectangle rank, that excess decades collapse into
  `"Other"`, and that excess rectangles get no assigned decade. Plus:
  `mondrian_treemap(df)` returns a `go.Figure` with one trace per
  digitized rectangle.

## Migration notes

`notebooks/02_chart_prototyping.ipynb`: the Mondrian markdown cell's
inspection prompt is updated to describe the new hover-based inspection
("does each rectangle's hover show a plausible decade/count, and does the
overall shape still read as the source composition?"); the code cell is
unchanged (`charts.mondrian_treemap(cleaned).show()` still works — same
function name and signature once graduated).
