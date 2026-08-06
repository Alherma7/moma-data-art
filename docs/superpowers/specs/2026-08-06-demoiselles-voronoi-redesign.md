# Demoiselles d'Avignon Voronoi redesign

## Concept

Same principle as the Mondrian chart: the painting's own real geometry is
the data container, revealed on hover. Rectangles don't fit Picasso's
fractured, angular style, so this chart uses a Voronoi diagram computed
over the canvas of `images/les_demoiselles_davignon.png` instead — cells
carved out of the picture plane, echoing Picasso's own faceted shapes,
holding real MoMA collection data.

Unlike Mondrian, where color is always the painting's real color and data
lives only in the hover text, here **color is a data encoding** (gender)
because the painting itself has no consistent per-region color scheme to
preserve — Cubist faceting doesn't map to flat regions the way Mondrian's
primary-color blocks do.

## Data mapping

- **Gender per person**: classified per credited person (not per artwork)
  from the raw MoMA `Gender` field. Checked against the real distinct
  values in `data/raw/Artworks.json`:

  | Raw value | Count | Bucket |
  |---|---|---|
  | `male` | 139,556 | Hombre |
  | `female` | 23,888 | Mujer |
  | `female (transwoman)` | 62 | Transgénero |
  | `male (trans? ftm?)` | 11 | Transgénero |
  | `transgender woman` | 1 | Transgénero |
  | `` (empty) | 1,713 | discarded |
  | `non-binary` | 13 | discarded |
  | `gender non-conforming` | 2 | discarded |

  Rule, evaluated in this order: value contains "trans" → Transgénero;
  else starts with "female" → Mujer; else starts with "male" → Hombre;
  anything else is discarded from the count. Checking "trans" first is
  what correctly buckets `female (transwoman)` and `male (trans? ftm?)`
  into Transgénero instead of leaking into Mujer/Hombre by prefix match.
  The three discarded values (empty, non-binary, gender non-conforming)
  are genuinely distinct categories or missing data, not wording variants
  of the three buckets — nothing is being incorrectly dropped.

- **Decade**: `Decade_acquired`, same field and logic as Mondrian.

- **Cell assignment**: count (decade, gender) combinations, e.g.
  `("1960s", "Mujer")`, and rank them by count descending. Voronoi cells
  are ranked by area descending. Combinations are zipped to cells by
  rank, generalizing Mondrian's `_assign_decades_to_rectangles` so the
  "label" is a `(decade, gender)` tuple instead of a bare decade. If
  there are more combinations than cells, the smallest are pooled into an
  "Other" entry and re-sorted (identical logic to Mondrian). If there are
  more cells than combinations — expected here, since (decade × gender)
  is a much finer split than decade alone — the excess cells are left
  unassigned, rendered with no hover and no data color (same neutral
  treatment as Mondrian's unassigned rectangles).

- **Color** = gender of the combination assigned to that cell. Unassigned
  cells get a neutral, undifferentiated fill.

- **Hover** = decade + artwork count only (e.g. "1960s · 42 obras").
  Gender is not repeated in the hover text since it's already
  communicated by the cell's color and the legend.

- **Legend**: Plotly doesn't auto-generate a legend for `fill='toself'`
  traces without empty rendered points, so three invisible proxy traces
  (one per gender bucket, zero-length geometry, `showlegend=True`,
  `name=<gender>`, matching fill color) are added purely to produce the
  three legend entries.

## Geometry

- **Face contours**: ~5 rough polygons (one per figure in the painting),
  hand-digitized from `images/les_demoiselles_davignon.png` the same way
  as Mondrian's rectangles — proposed as starting coordinates by Claude,
  adjusted cell-by-cell in the notebook by the user against the real
  image.
- **Seed points**: a jittered grid (fixed seed via `config.RANDOM_STATE`)
  covering the *entire* canvas — figures and background alike, per the
  user's direction that data isn't restricted to the background. Points
  falling inside a face contour are discarded before tessellation, so
  faces are never subdivided by seed density. ~40 points as a starting
  density, tunable in the notebook once the first render is visible.
- **Voronoi diagram**: `scipy.spatial.Voronoi` over the surviving seed
  points. Infinite regions are bounded to the canvas rectangle (standard
  bounded-Voronoi clipping).
- **Face clipping**: every resulting cell is intersected against the face
  contours with `shapely` (`cell.difference(face_polygon)` for any face
  it overlaps), so no data cell geometrically invades a face even though
  raw Voronoi regions can extend past their generating point.
- **Faces as decoration**: face contours are drawn as flat, undivided
  fills with no hover and no ranked data — analogous to Mondrian's
  background rectangles — in the neutral face color from the palette.
  It is expected that many cells (especially ones split or shrunk by
  face clipping) will end up small or oddly shaped; this is accepted as
  a known property of a first prototype, not something to special-case
  away.
- **No extra decoration**: unlike Mondrian, no overshoot lines or
  cross-tick ornaments for this first version.

## Palette

Representational tones drawn from the painting, but functioning here as
a genuine data encoding rather than the painting's literal colors:

| Role | Color |
|---|---|
| Mujer | `#C97B63` (terracotta rose) |
| Hombre | `#6E8CA0` (grey-blue) |
| Transgénero | `#D4A24C` (golden ochre) |
| Face (decorative, no data) | `#E8DCC8` (neutral beige) |
| Plot background | `#F2EADD` (light cream, matched to the painting's overall tone) |

Added to `src/config.py` as a new `"demoiselles"` entry in `PALETTES`,
alongside the existing `"mondrian"` entry.

## Development workflow

Notebook-first, identical process to Mondrian: the user runs and verifies
every cell themselves in `notebooks/04_demoiselles_prototyping.ipynb`;
Claude prepares cells but never executes them on the user's behalf. Once
the prototype is validated end-to-end against real data, the code
graduates into `src/demoiselles_geometry.py` (face contours, seed
generation, Voronoi computation, face-clipping, cell-to-rank assignment
helpers — mirroring `src/mondrian_geometry.py`'s structure) and
`src/charts.py` gains a new `demoiselles_voronoi(df)` function alongside
the existing `mondrian_treemap(df)`.

## Dependencies

`scipy` (for `scipy.spatial.Voronoi`) and `shapely` (for polygon
clipping/difference) are added back to `requirements.txt` — both were
removed during the project reset since the old, different, weighted
Voronoi-treemap approach (`src/voronoi_treemap.py`, deleted) no longer
existed to need them.

## Testing

Same shape as Mondrian's test suite:
- `tests/test_demoiselles_geometry.py`: seed-point generation excludes
  points inside face contours (deterministic, given the fixed random
  seed); bounded-Voronoi clipping keeps all cells within canvas bounds;
  face-clipping actually removes face-overlapping area from a cell
  (synthetic fixture); rank-assignment generalizes correctly to
  `(decade, gender)` tuples, including the "Other" pooling and re-sort
  behavior already proven for Mondrian's decade-only case.
- `tests/test_charts.py`: `demoiselles_voronoi(df)` returns a
  `go.Figure`; the highest-ranked (decade, gender) combination lands on
  the largest cell; hover text contains decade + count but not gender;
  legend proxy traces exist for all three gender buckets with the
  correct colors; unassigned cells have empty hover, matching the
  `hoveron='fills'` + `text=`/`hoverinfo="text"` pattern already fixed
  for Mondrian (never `hovertemplate`, which plotly.js silently discards
  on fill hovers).

## Migration notes

No prior Demoiselles code exists in the repo (deleted in full during the
2026-08-06 project reset) — this is a fresh build, not a migration.
