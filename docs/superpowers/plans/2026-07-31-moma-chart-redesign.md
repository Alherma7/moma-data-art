# MoMA Chart Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 3 Pipeline A chart functions (`mondrian_treemap`, `demoiselles_radar`, `dance_circular_bar`) with designs ported from the user's original Tableau Public dashboards, which read as their target paintings where the v1 designs didn't.

**Architecture:** Extend `src/data.py` with 3 new derived columns (`Credit_category`, `Num_participants`, `Decade_acquired`/`Year_acquired`), add a new from-scratch weighted-Voronoi-treemap module (`src/voronoi_treemap.py`), then rewrite the 3 functions in `src/charts.py` in place (2 of them renamed to match their new chart type).

**Tech Stack:** Python 3.11, pandas, NumPy, Plotly, Pillow, SciPy (`scipy.spatial.Voronoi`), Shapely (polygon union/clipping), pytest.

**Design spec:** `docs/superpowers/specs/2026-07-31-moma-chart-redesign.md`

## Global Constraints

- `RANDOM_STATE = 42` (from `src/config.py`) for any randomness — used here as the seed for `voronoi_treemap.sample_points`'s `random.Random` instance.
- No new top-level dependency without adding it to `requirements.txt` in the same task that first imports it.
- `src/charts.py` keeps one function per painting, each still returning a `plotly.graph_objects.Figure`, still consumed the same way by `build_site.py` (not yet built) — the public call sites don't change shape, only 2 of 3 function names change (`demoiselles_radar` → `demoiselles_voronoi`, `dance_circular_bar` → `dance_scatter`).
- Every function in `src/data.py` and `src/voronoi_treemap.py` needs a unit test in `tests/` before use elsewhere, per the project's existing testing discipline.
- Pipeline A has no numeric pass/fail gate for the charts themselves (per the original design spec, this is qualitative) — `tests/test_charts.py` only checks structural properties (a `Figure` is returned, it has the right number of traces/points), never "does it look right."

---

### Task 1: `Credit_category` classifier

**Files:**
- Modify: `src/data.py`
- Modify: `tests/test_data.py`

**Interfaces:**
- Produces: `data.classify_credit(credit_line) -> str` — consumed by Task 3 (`clean_artworks`) and Task 6 (`mondrian_treemap`).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_data.py`:

```python
def test_classify_credit_matches_known_keywords():
    assert data.classify_credit("Gift of the artist") == "donated/gifts"
    assert data.classify_credit("Purchase") == "purchase/acquired"
    assert data.classify_credit("Mrs. Simon Guggenheim Fund") == "fund/institutions"
    assert data.classify_credit(None) == "other/unknown"
    assert data.classify_credit("Totally unrecognized text") == "other/unknown"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data.py::test_classify_credit_matches_known_keywords -v`
Expected: FAIL with `AttributeError: module 'src.data' has no attribute 'classify_credit'`

- [ ] **Step 3: Add `classify_credit` to `src/data.py`**

Add this module-level dict near the top of `src/data.py`, alongside `_MEDIUM_CATEGORIES` and `_REGION_MAP`:

```python
_CREDIT_CATEGORIES = {
    "fund/institutions": ["fund", "foundation", "endowment", "charitable trust", "council", "university", "museum", "comitte"],
    "purchase/acquired": ["purchase", "puchase", "acquired", "acquisition", "exchange", "transferred", "collection", "commissioned"],
    "donated/gifts": ["donated", "donor", "gift", "giff", "given", "generosity", "courtesy", "bequest", "estate", "testamentary"],
    "individual": ["j. b. neumann", "abraham", "blanchette", "mr.", "ms.", "individual"],
}
```

Then add this function anywhere below `classify_medium`:

```python
def classify_credit(credit_line) -> str:
    """Bucket a raw CreditLine string into a coarse acquisition-source
    category. Ported from the original PRA1 notebook's classify_credit(),
    validated there against this same field."""
    if pd.isna(credit_line):
        return "other/unknown"
    c = credit_line.lower().strip()
    for category, keywords in _CREDIT_CATEGORIES.items():
        if any(keyword in c for keyword in keywords):
            return category
    return "other/unknown"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data.py::test_classify_credit_matches_known_keywords -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data.py tests/test_data.py
git commit -m "feat: add Credit_category classifier"
```

---

### Task 2: `Num_participants` counter

**Files:**
- Modify: `src/data.py`
- Modify: `tests/test_data.py`

**Interfaces:**
- Produces: `data.count_participants(genders: list) -> int` — consumed by Task 3 (`clean_artworks`) and Task 8 (`dance_scatter`).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_data.py`:

```python
def test_count_participants_counts_list_length():
    assert data.count_participants(["male", "female"]) == 2
    assert data.count_participants(["male"]) == 1
    assert data.count_participants([]) == 0
    assert data.count_participants(None) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data.py::test_count_participants_counts_list_length -v`
Expected: FAIL with `AttributeError: module 'src.data' has no attribute 'count_participants'`

- [ ] **Step 3: Add `count_participants` to `src/data.py`**

Add anywhere below `classify_credit`:

```python
def count_participants(genders) -> int:
    """Number of constituents credited on an artwork — Artworks.json's
    Gender field is a list with one entry per credited artist, so its
    length is the participant count directly (no regex parsing needed,
    unlike the original CSV-based notebook's count_participants())."""
    return len(genders) if isinstance(genders, list) else 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data.py::test_count_participants_counts_list_length -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data.py tests/test_data.py
git commit -m "feat: add Num_participants counter"
```

---

### Task 3: Wire `Credit_category`, `Num_participants`, `Decade_acquired`/`Year_acquired` into `clean_artworks`

**Files:**
- Modify: `src/data.py`
- Modify: `tests/test_data.py`

**Interfaces:**
- Consumes: `classify_credit` (Task 1), `count_participants` (Task 2), `classify_decade` (existing, applied here to `DateAcquired` instead of `Date`).
- Produces: `clean_artworks(df)` gains 4 new output columns: `Credit_category`, `Num_participants`, `Decade_acquired`, `Year_acquired` — consumed by Task 6 (`mondrian_treemap`), Task 7 (`demoiselles_voronoi`), Task 8 (`dance_scatter`).

- [ ] **Step 1: Update the failing test**

`tests/test_data.py` already has `test_clean_artworks_adds_expected_columns`. Replace it entirely with:

```python
def test_clean_artworks_adds_expected_columns():
    df = pd.DataFrame({
        "Medium": ["Oil on canvas"],
        "Gender": [["male"]],
        "Nationality": [["American"]],
        "Date": ["1913"],
        "DateAcquired": ["1996-04-09"],
        "CreditLine": ["Gift of the artist"],
    })
    cleaned = data.clean_artworks(df)
    for column in [
        "Medium_category", "Gender_simple", "Nationality_list",
        "Region_list", "Decade", "Year_min",
        "Credit_category", "Num_participants", "Decade_acquired", "Year_acquired",
    ]:
        assert column in cleaned.columns
    assert cleaned.loc[0, "Medium_category"] == "painting"
    assert cleaned.loc[0, "Decade"] == "1910s"
    assert cleaned.loc[0, "Credit_category"] == "donated/gifts"
    assert cleaned.loc[0, "Num_participants"] == 1
    assert cleaned.loc[0, "Decade_acquired"] == "1990s"
    assert cleaned.loc[0, "Year_acquired"] == 1996
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data.py::test_clean_artworks_adds_expected_columns -v`
Expected: FAIL with `KeyError: 'CreditLine'` or a `KeyError`/`AssertionError` about a missing column (the current `clean_artworks` doesn't read `CreditLine`/`DateAcquired` yet).

- [ ] **Step 3: Update `clean_artworks` in `src/data.py`**

Replace the current `clean_artworks` function body with:

```python
def clean_artworks(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all categorization functions to a raw Artworks dataframe."""
    df = df.copy()
    df["Medium_category"] = df["Medium"].apply(classify_medium)
    df["Gender_simple"] = df["Gender"].apply(simplify_gender)
    df["Nationality_list"] = df["Nationality"].apply(clean_nationalities)
    df["Region_list"] = df["Nationality_list"].apply(
        lambda names: [get_region(n) for n in names] if names else ["unknown"]
    )
    df[["Decade", "Year_min"]] = df["Date"].apply(
        lambda d: pd.Series(classify_decade(d))
    )
    df["Credit_category"] = df["CreditLine"].apply(classify_credit)
    df["Num_participants"] = df["Gender"].apply(count_participants)
    df[["Decade_acquired", "Year_acquired"]] = df["DateAcquired"].apply(
        lambda d: pd.Series(classify_decade(d))
    )
    return df
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data.py::test_clean_artworks_adds_expected_columns -v`
Expected: PASS

- [ ] **Step 5: Run the full data test file**

Run: `pytest tests/test_data.py -v`
Expected: PASS (all tests, including the 2 added in Tasks 1-2)

- [ ] **Step 6: Commit**

```bash
git add src/data.py tests/test_data.py
git commit -m "feat: wire Credit_category/Num_participants/Decade_acquired into clean_artworks"
```

---

### Task 4: Weighted point sampling (`src/voronoi_treemap.py`, part 1)

**Files:**
- Create: `src/voronoi_treemap.py`
- Test: `tests/test_voronoi_treemap.py`

**Interfaces:**
- Produces: `voronoi_treemap.sample_points(weights: dict[str, float], rng: random.Random, total_points: int = 2000) -> dict[str, list[tuple[float, float]]]` — consumed by Task 5 (`voronoi_cells`) and Task 7 (`demoiselles_voronoi`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_voronoi_treemap.py`:

```python
import random

from src import voronoi_treemap


def test_sample_points_allocates_proportional_to_weight():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 3.0}, rng, total_points=400)
    assert set(points.keys()) == {"a", "b"}
    assert len(points["a"]) == 100
    assert len(points["b"]) == 300
    for group_points in points.values():
        for x, y in group_points:
            assert 0.0 <= x <= 1.0
            assert 0.0 <= y <= 1.0


def test_sample_points_gives_every_group_at_least_one_point():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 0.001}, rng, total_points=10)
    assert len(points["b"]) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_voronoi_treemap.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.voronoi_treemap'`

- [ ] **Step 3: Create `src/voronoi_treemap.py`**

```python
import random


def sample_points(weights: dict, rng: random.Random, total_points: int = 2000) -> dict:
    """Sample points within the unit square [0,1]x[0,1], allocated to each
    group proportional to its weight (largest-remainder method, so counts
    sum to exactly total_points), with every group guaranteed at least 1
    point so it still produces a valid Voronoi cell downstream."""
    groups = list(weights.keys())
    total_weight = sum(weights.values())
    raw_counts = {g: total_points * weights[g] / total_weight for g in groups}
    counts = {g: int(raw_counts[g]) for g in groups}

    remainder = total_points - sum(counts.values())
    by_fractional_part = sorted(
        groups, key=lambda g: raw_counts[g] - counts[g], reverse=True
    )
    for g in by_fractional_part[:remainder]:
        counts[g] += 1

    return {
        g: [(rng.random(), rng.random()) for _ in range(max(1, counts[g]))]
        for g in groups
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_voronoi_treemap.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/voronoi_treemap.py tests/test_voronoi_treemap.py
git commit -m "feat: add weighted point sampling for the Voronoi treemap"
```

---

### Task 5: Bounded, merged Voronoi cells (`src/voronoi_treemap.py`, part 2)

**Files:**
- Modify: `src/voronoi_treemap.py`
- Modify: `tests/test_voronoi_treemap.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `sample_points` output (Task 4).
- Produces: `voronoi_treemap.voronoi_cells(points: dict[str, list[tuple[float, float]]]) -> dict[str, shapely.geometry.Polygon]` — consumed by Task 7 (`demoiselles_voronoi`).

- [ ] **Step 1: Add `scipy` and `shapely` to `requirements.txt`**

`requirements.txt` becomes:

```
pandas
numpy
pillow
plotly
pyarrow
pytest
scipy
shapely
```

Run: `pip install scipy shapely` (scipy is likely already present; shapely needs installing).

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_voronoi_treemap.py`:

```python
import pytest


def test_voronoi_cells_returns_one_polygon_per_group():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 1.0}, rng, total_points=200)
    cells = voronoi_treemap.voronoi_cells(points)
    assert set(cells.keys()) == {"a", "b"}
    for polygon in cells.values():
        assert polygon.is_valid
        assert polygon.area > 0


def test_voronoi_cells_areas_are_roughly_proportional_to_weight():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 3.0}, rng, total_points=800)
    cells = voronoi_treemap.voronoi_cells(points)
    ratio = cells["b"].area / cells["a"].area
    assert 2.0 < ratio < 4.0  # target 3.0; generous tolerance for sampling noise


def test_voronoi_cells_cover_the_unit_square_without_gaps():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 1.0, "c": 1.0}, rng, total_points=600)
    cells = voronoi_treemap.voronoi_cells(points)
    total_area = sum(polygon.area for polygon in cells.values())
    assert total_area == pytest.approx(1.0, abs=0.02)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_voronoi_treemap.py -v`
Expected: FAIL with `AttributeError: module 'src.voronoi_treemap' has no attribute 'voronoi_cells'`

- [ ] **Step 4: Add `voronoi_cells` to `src/voronoi_treemap.py`**

Update the top of `src/voronoi_treemap.py` (the existing `import random` line) to:

```python
import random

import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

_BOUNDS = box(0, 0, 1, 1)
```

Then add this function below `sample_points`:

```python
def voronoi_cells(points: dict) -> dict:
    """Compute a Voronoi diagram over all groups' combined points, clipped
    to the unit square, with same-group cells merged into one polygon.

    Every point is mirrored across all 4 edges of the unit square before
    running scipy's Voronoi — a standard trick that gives every original
    (non-mirrored) point a finite region, since an infinite/unbounded
    Voronoi cell can't be clipped to a polygon.
    """
    groups = list(points.keys())
    labels = []
    coords = []
    for group in groups:
        for x, y in points[group]:
            labels.append(group)
            coords.append((x, y))
    coords = np.array(coords)
    n = len(coords)

    mirrored = np.vstack([
        coords,
        np.column_stack([-coords[:, 0], coords[:, 1]]),
        np.column_stack([2 - coords[:, 0], coords[:, 1]]),
        np.column_stack([coords[:, 0], -coords[:, 1]]),
        np.column_stack([coords[:, 0], 2 - coords[:, 1]]),
    ])
    vor = Voronoi(mirrored)

    polygons_by_group = {}
    for i in range(n):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        vertices = [vor.vertices[v] for v in region]
        polygon = Polygon(vertices).intersection(_BOUNDS)
        if polygon.is_empty:
            continue
        polygons_by_group.setdefault(labels[i], []).append(polygon)

    return {
        group: unary_union(polys)
        for group, polys in polygons_by_group.items()
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_voronoi_treemap.py -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/voronoi_treemap.py tests/test_voronoi_treemap.py requirements.txt
git commit -m "feat: add bounded, merged Voronoi cell computation"
```

---

### Task 6: Rewrite `mondrian_treemap`

**Files:**
- Modify: `src/charts.py`
- Modify: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["mondrian"]`; a cleaned dataframe with `Decade_acquired`/`Credit_category` columns (Task 3).
- Produces: `charts.mondrian_treemap(df) -> plotly.graph_objects.Figure` (same name/signature, new grouping) — consumed by `build_site.py` (not yet built).

- [ ] **Step 1: Replace the test fixture and the Mondrian test**

Replace all of `tests/test_charts.py` with:

```python
import pandas as pd
import plotly.graph_objects as go

from src import charts


def _sample_df():
    return pd.DataFrame({
        "Decade_acquired": ["1960s", "1960s", "1970s", "1990s", "1990s", "2000s", "2010s", "2010s"],
        "Credit_category": [
            "donated/gifts", "purchase/acquired", "donated/gifts", "purchase/acquired",
            "individual", "other/unknown", "donated/gifts", "purchase/acquired",
        ],
        "Decade": ["1900s", "1910s", "1910s", "1920s", "1920s", "1930s", "1930s", "1940s"],
        "Gender_simple": ["male", "female", "male", "female", "mixed", "male", "female", "male"],
        "Num_participants": [1, 2, 3, 1, 2, 1, 4, 2],
    })


def test_mondrian_treemap_returns_figure_with_data():
    fig = charts.mondrian_treemap(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
```

(The Demoiselles and Dance tests are added back in Tasks 7 and 8.)

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py -v`
Expected: FAIL with `KeyError: 'Department'` — the current `mondrian_treemap` still groups by `Department`/`Medium_category`, neither of which exists in the new fixture.

- [ ] **Step 3: Rewrite `mondrian_treemap` in `src/charts.py`**

Replace the current `mondrian_treemap` function with:

```python
def mondrian_treemap(df):
    """Treemap of artwork counts by acquisition decade and credit category,
    colored to evoke Mondrian's grid of primary-color blocks: the 3 most
    active decades get red/blue/yellow, every other decade gets black."""
    palette = config.PALETTES["mondrian"]
    known = df[df["Decade_acquired"] != "unknown"]
    counts = (
        known.groupby(["Decade_acquired", "Credit_category"])
        .size()
        .reset_index(name="count")
    )
    decade_totals = counts.groupby("Decade_acquired")["count"].sum()
    top_decades = decade_totals.nlargest(5).index.tolist()
    top_decades_sorted = sorted(top_decades, key=lambda d: int(d.rstrip("s")))
    counts = counts[counts["Decade_acquired"].isin(top_decades_sorted)]

    primaries = [palette["red"], palette["blue"], palette["yellow"]]
    color_map = {
        decade: (primaries[i] if i < len(primaries) else palette["black"])
        for i, decade in enumerate(top_decades_sorted)
    }

    fig = px.treemap(
        counts,
        path=["Decade_acquired", "Credit_category"],
        values="count",
        color="Decade_acquired",
        color_discrete_map=color_map,
    )
    fig.update_traces(marker=dict(line=dict(color=palette["black"], width=3)))
    fig.update_layout(paper_bgcolor=palette["background"], margin=dict(t=20, l=0, r=0, b=0))
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: rewrite Mondrian treemap grouped by acquisition decade and credit category"
```

---

### Task 7: Add `demoiselles_voronoi` (replaces `demoiselles_radar`)

**Files:**
- Modify: `src/charts.py`
- Modify: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["demoiselles"]`, `config.RANDOM_STATE`; `voronoi_treemap.sample_points`/`voronoi_cells` (Tasks 4-5); a cleaned dataframe with `Decade`/`Gender_simple` columns (Task 3, existing); `_sample_df()` fixture (Task 6).
- Produces: `charts.demoiselles_voronoi(df) -> plotly.graph_objects.Figure` — consumed by `build_site.py` (not yet built). This function replaces `demoiselles_radar`, which is deleted in this task.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_charts.py`:

```python
def test_demoiselles_voronoi_returns_one_trace_per_decade():
    df = _sample_df()
    fig = charts.demoiselles_voronoi(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == df["Decade"].nunique()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py::test_demoiselles_voronoi_returns_one_trace_per_decade -v`
Expected: FAIL with `AttributeError: module 'src.charts' has no attribute 'demoiselles_voronoi'`

- [ ] **Step 3: Replace `demoiselles_radar` with `demoiselles_voronoi` in `src/charts.py`**

Update the imports at the top of `src/charts.py` to:

```python
import random

import plotly.express as px
import plotly.graph_objects as go

from . import config, voronoi_treemap
```

Delete the existing `demoiselles_radar` function entirely, and add these two functions in its place:

```python
def _interpolate_hex(color_a: str, color_b: str, t: float) -> str:
    """Linearly interpolate between two '#RRGGBB' colors at t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    a = tuple(int(color_a[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(color_b[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def demoiselles_voronoi(df):
    """Voronoi treemap with one cell per decade, sized by artwork count and
    colored by gender ratio (pale pink = balanced/female-leaning, dark
    maroon = male-dominated), evoking the painting's fragmented cubist
    planes."""
    palette = config.PALETTES["demoiselles"]
    known = df[df["Decade"] != "unknown"]
    weights = known["Decade"].value_counts().to_dict()

    rng = random.Random(config.RANDOM_STATE)
    points = voronoi_treemap.sample_points(weights, rng)
    cells = voronoi_treemap.voronoi_cells(points)

    fig = go.Figure()
    for decade, polygon in cells.items():
        subset = known[known["Decade"] == decade]
        male = (subset["Gender_simple"] == "male").sum()
        female = (subset["Gender_simple"] == "female").sum()
        ratio = male / (male + female) if (male + female) > 0 else 0.5
        color = _interpolate_hex(palette["pink"], palette["brown"], ratio)

        x, y = polygon.exterior.xy
        fig.add_trace(
            go.Scatter(
                x=list(x),
                y=list(y),
                fill="toself",
                fillcolor=color,
                line=dict(color=palette["terracotta"], width=1),
                name=decade,
                mode="lines",
            )
        )
    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x"),
        showlegend=True,
    )
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py -v`
Expected: PASS (2 tests: Mondrian from Task 6, Demoiselles here)

- [ ] **Step 5: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: replace Demoiselles radar chart with a Voronoi treemap"
```

---

### Task 8: Add `dance_scatter` (replaces `dance_circular_bar`)

**Files:**
- Modify: `src/charts.py`
- Modify: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["dance"]`, `config.GEOMETRIZE_CONFIGS["dance"]["image"]` (existing path to `images/dance_i.png`); a cleaned dataframe with `Decade`/`Num_participants` columns (Task 3); `_sample_df()` fixture (Task 6).
- Produces: `charts.dance_scatter(df) -> plotly.graph_objects.Figure` — consumed by `build_site.py` (not yet built). This function replaces `dance_circular_bar`, which is deleted in this task.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_charts.py`:

```python
def test_dance_scatter_returns_one_point_per_group_work_decade():
    df = _sample_df()
    fig = charts.dance_scatter(df)
    assert isinstance(fig, go.Figure)
    expected_decades = df[df["Num_participants"] >= 2]["Decade"].nunique()
    assert len(fig.data[0].x) == expected_decades
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py::test_dance_scatter_returns_one_point_per_group_work_decade -v`
Expected: FAIL with `AttributeError: module 'src.charts' has no attribute 'dance_scatter'`

- [ ] **Step 3: Replace `dance_circular_bar` with `dance_scatter` in `src/charts.py`**

Add this import at the top of `src/charts.py`, alongside the existing imports:

```python
from PIL import Image
```

Delete the existing `dance_circular_bar` function entirely, and add this in its place:

```python
def dance_scatter(df):
    """Scatter of group-authored-work count vs. total participants per
    decade, plotted over the Dance I painting as a background image,
    echoing Matisse's flat colors and the ring of collaborating dancers."""
    palette = config.PALETTES["dance"]
    colors = [palette["orange"], palette["green"], palette["blue"]]

    grouped = df[(df["Decade"] != "unknown") & (df["Num_participants"] >= 2)]
    by_decade = (
        grouped.groupby("Decade")
        .agg(num_group_works=("Decade", "size"), num_participants=("Num_participants", "sum"))
        .reset_index()
    )
    by_decade = by_decade.sort_values(
        "Decade", key=lambda s: s.str.rstrip("s").astype(int)
    )

    image = Image.open(config.GEOMETRIZE_CONFIGS["dance"]["image"])

    fig = go.Figure(
        go.Scatter(
            x=by_decade["num_group_works"],
            y=by_decade["num_participants"],
            mode="markers",
            marker=dict(
                size=14,
                color=[colors[i % len(colors)] for i in range(len(by_decade))],
                line=dict(color="white", width=1),
            ),
            text=by_decade["Decade"],
            hovertemplate="%{text}<br>Group works: %{x}<br>Participants: %{y}<extra></extra>",
        )
    )
    fig.add_layout_image(
        dict(
            source=image,
            xref="paper",
            yref="paper",
            x=0,
            y=1,
            sizex=1,
            sizey=1,
            sizing="stretch",
            layer="below",
            opacity=0.9,
        )
    )
    fig.update_layout(
        xaxis=dict(title="Group-authored works"),
        yaxis=dict(title="Total participants"),
        margin=dict(t=20, l=60, r=20, b=40),
    )
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py -v`
Expected: PASS (3 tests: Mondrian, Demoiselles, Dance)

- [ ] **Step 5: Run the entire test suite**

Run: `pytest -v`
Expected: PASS (every test across `test_data.py`, `test_voronoi_treemap.py`, `test_charts.py`, plus the pre-existing Geometrize tests)

- [ ] **Step 6: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: replace Dance circular bar chart with a scatter over the painting"
```

---

### Task 9: Update the chart prototyping notebook to call the renamed functions

**Files:**
- Modify: `notebooks/02_chart_prototyping.ipynb`

**Interfaces:**
- Consumes: `charts.mondrian_treemap`, `charts.demoiselles_voronoi`, `charts.dance_scatter` (Tasks 6-8).

This notebook was created earlier (before this redesign) and still calls the old `demoiselles_radar`/`dance_circular_bar` names. No structural change is needed, only the two renamed calls.

- [ ] **Step 1: Update the two renamed calls**

In `notebooks/02_chart_prototyping.ipynb`, change the cell containing `charts.demoiselles_radar(cleaned).show()` to:

```python
charts.demoiselles_voronoi(cleaned).show()
```

And change the cell containing `charts.dance_circular_bar(cleaned).show()` to:

```python
charts.dance_scatter(cleaned).show()
```

Leave every other cell (the markdown inspection prompts, the Mondrian cell, the findings cell) unchanged.

- [ ] **Step 2: Commit**

```bash
git add notebooks/02_chart_prototyping.ipynb
git commit -m "docs: update chart prototyping notebook for renamed chart functions"
```

Note: per the project's notebook-execution preference, running this notebook and recording qualitative findings (does each chart now read as its painting?) is a follow-up step for the user to do in Jupyter — not part of this plan's automated tasks.
