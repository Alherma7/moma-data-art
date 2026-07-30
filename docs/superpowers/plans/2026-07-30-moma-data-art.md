# MoMA Data Art Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Python project that (a) turns real MoMA collection metadata into charts styled to evoke three MoMA paintings, and (b) reimplements the Geometrize image-to-polygon technique from scratch, then combines both into a static site published on GitHub Pages with a weekly automated data refresh.

**Architecture:** Two independent pipelines (`src/charts.py` for data→form charts, `src/geometrize/` for the hill-climbing engine) share one cleaned dataset (`src/data.py`) and are assembled by `src/build_site.py` into a static HTML page. A GitHub Actions workflow refreshes the MoMA data and chart outputs on a schedule; Geometrize outputs are cached and reused since they don't depend on the metadata.

**Tech Stack:** Python 3.11, pandas, Plotly, Pillow, NumPy, pytest, GitHub Actions, GitHub Pages.

**Design spec:** `docs/superpowers/specs/2026-07-30-moma-data-art-design.md`

## Global Constraints

- Python 3.11, dependencies pinned in `requirements.txt`: `pandas`, `numpy`, `pillow`, `plotly`, `pyarrow`, `pytest`.
- `RANDOM_STATE = 42` everywhere randomness is used (Geometrize's `random.Random` seed), for reproducible output between runs.
- No JS framework for the site — plain HTML/CSS, Plotly figures exported as self-contained HTML fragments, Geometrize output as inline SVG.
- Package layout is fixed by the spec: `src/`, `src/geometrize/`, `tests/`, `notebooks/`, `data/{raw,processed}`, `images/`, `outputs/{charts,geometrize,site}`.
- Every function in `src/data.py` and the metric in `src/geometrize/evaluate.py` needs a unit test in `tests/` before use elsewhere (per `structuring-ml-projects`).
- The three v1 paintings and their internal keys (used throughout config/code): `mondrian`, `demoiselles`, `dance`.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `src/geometrize/__init__.py`
- Create: `src/config.py`
- Create: `README.md`
- Create: `RESOURCES.md`
- Create: `images/mondrian_composition.jpg` (copied)
- Create: `images/les_demoiselles_davignon.png` (copied)
- Create: `images/dance_i.png` (copied)
- Create: `data/raw/Artworks.json` (copied, bootstrap only)
- Create: `data/raw/Artists.json` (copied, bootstrap only)

**Interfaces:**
- Produces: `config.RANDOM_STATE: int`, `config.ROOT_DIR/DATA_RAW_DIR/DATA_PROCESSED_DIR/IMAGES_DIR/OUTPUTS_DIR: Path`, `config.MOMA_ARTWORKS_URL/MOMA_ARTISTS_URL: str`, `config.PALETTES: dict`, `config.GEOMETRIZE_CONFIGS: dict` — every later task imports from this module.

- [ ] **Step 1: Create the directory tree and empty package markers**

```bash
mkdir -p data/raw data/processed images notebooks src/geometrize tests \
  outputs/charts outputs/geometrize outputs/site .github/workflows
touch src/__init__.py src/geometrize/__init__.py
```

- [ ] **Step 2: Copy the source images and raw MoMA data from the original PRA1 project**

```bash
cp "C:/Users/alher/Desktop/CIENCIA DE DATOS/VISUALIZACION DE DATOS/PRA1/VARIOS/piet-mondrian-paintings.jpg" images/mondrian_composition.jpg
cp "C:/Users/alher/Desktop/CIENCIA DE DATOS/VISUALIZACION DE DATOS/PRA1/VARIOS/Les Demoiselles d'Avignon.png" "images/les_demoiselles_davignon.png"
cp "C:/Users/alher/Desktop/CIENCIA DE DATOS/VISUALIZACION DE DATOS/PRA1/VARIOS/DANCE I.png" images/dance_i.png
cp "C:/Users/alher/Desktop/CIENCIA DE DATOS/VISUALIZACION DE DATOS/PRA1/collection-v2025-11-25/Artworks.json" data/raw/Artworks.json
cp "C:/Users/alher/Desktop/CIENCIA DE DATOS/VISUALIZACION DE DATOS/PRA1/collection-v2025-11-25/Artists.json" data/raw/Artists.json
```

Note: `mondrian_composition.jpg` is a generic Mondrian-style grid composition
bundled with the original project, not verified against a specific MoMA
accession title — use a neutral caption ("Mondrian-style composition") in
the site unless you confirm and update it to a specific MoMA-catalogued
title later.

- [ ] **Step 3: Write `src/config.py`**

```python
from pathlib import Path

RANDOM_STATE = 42

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
IMAGES_DIR = ROOT_DIR / "images"
OUTPUTS_DIR = ROOT_DIR / "outputs"

MOMA_ARTWORKS_URL = "https://raw.githubusercontent.com/MoMA/collection/master/Artworks.json"
MOMA_ARTISTS_URL = "https://raw.githubusercontent.com/MoMA/collection/master/Artists.json"

PALETTES = {
    "mondrian": {
        "red": "#D40920",
        "blue": "#1356A2",
        "yellow": "#F7D842",
        "black": "#111111",
        "background": "#F2F0E6",
    },
    "demoiselles": {
        "terracotta": "#B5651D",
        "pink": "#D9A5A0",
        "cream": "#E8DCC8",
        "brown": "#3B2A20",
        "background": "#EFE6D8",
    },
    "dance": {
        "orange": "#E2725B",
        "green": "#5C8A3A",
        "blue": "#3C6997",
    },
}

GEOMETRIZE_CONFIGS = {
    "mondrian": {
        "image": IMAGES_DIR / "mondrian_composition.jpg",
        "shape_kind": "rectangle",
        "n_shapes": 120,
        "n_candidates": 60,
        "n_refine": 20,
    },
    "demoiselles": {
        "image": IMAGES_DIR / "les_demoiselles_davignon.png",
        "shape_kind": "triangle",
        "n_shapes": 200,
        "n_candidates": 60,
        "n_refine": 20,
    },
    "dance": {
        "image": IMAGES_DIR / "dance_i.png",
        "shape_kind": "ellipse",
        "n_shapes": 150,
        "n_candidates": 60,
        "n_refine": 20,
    },
}
```

- [ ] **Step 4: Write `requirements.txt`, `pyproject.toml`, `.gitignore`**

`requirements.txt`:
```
pandas
numpy
pillow
plotly
pyarrow
pytest
```

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

`.gitignore`:
```
__pycache__/
*.pyc
.ipynb_checkpoints/
outputs/
data/processed/
```

- [ ] **Step 5: Write `README.md` and `RESOURCES.md`**

`README.md`:
```markdown
# MoMA Data Art

Data-driven visualizations styled after three MoMA paintings, plus a
from-scratch Python reimplementation of the Geometrize image-to-polygon
technique. Full design: `docs/superpowers/specs/2026-07-30-moma-data-art-design.md`.

## Progress

- [ ] Project scaffolding
- [ ] Data pipeline
- [ ] Chart functions (Mondrian, Demoiselles, Dance I)
- [ ] Geometrize engine
- [ ] Static site + GitHub Pages
- [ ] Scheduled data refresh

## Next steps

- [ ] Add Starry Night and Water Lilies (see spec's Extensibility section)
```

`RESOURCES.md`:
```markdown
## Papers / prior art

- **Primitive (Michael Fogleman)** (https://github.com/fogleman/primitive)
  Why: reference implementation of the hill-climbing shape-placement
  algorithm `src/geometrize/engine.py` reimplements in Python.

- **Geometrize** (https://www.samcodes.co.uk/project/geometrize-haxe-web/)
  Why: the manual web tool used in the original PRA1 project; this project
  automates the same idea end to end in Python.

## Comparable projects

- **Ken Flerlage's SVG-to-Tableau script** (`PRA1/VARIOS/Untitled.ipynb` in
  the original project)
  Why: prior technique for turning Geometrize SVG output into a Tableau
  chart; superseded here by rendering SVG directly on the static site.

## Dataset

- **MoMA Collection dataset** (https://github.com/MoMA/collection)
  Why: source of `Artworks.json`/`Artists.json`, the metadata driving every
  chart in this project.
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pyproject.toml .gitignore src/__init__.py \
  src/geometrize/__init__.py src/config.py README.md RESOURCES.md \
  images/ data/raw/
git commit -m "chore: scaffold project structure and config"
```

---

### Task 2: Data cleaning functions

**Files:**
- Create: `src/data.py`
- Test: `tests/test_data.py`

**Interfaces:**
- Consumes: `config.DATA_RAW_DIR`, `config.DATA_PROCESSED_DIR` (from Task 1)
- Produces: `data.classify_medium(medium: str) -> str`, `data.simplify_gender(genders: list) -> str`, `data.clean_nationalities(nationalities: list) -> list[str]`, `data.get_region(nationality: str) -> str`, `data.classify_decade(date) -> tuple[str, int | None]`, `data.clean_artworks(df: pd.DataFrame) -> pd.DataFrame` (adds columns `Medium_category`, `Gender_simple`, `Nationality_list`, `Region_list`, `Decade`, `Year_min`) — consumed by `charts.py` (Tasks 4-6) and `build_site.py` (Task 12).

**Correction found during implementation:** `Artworks.json` stores `Gender`
and `Nationality` as lists per constituent (e.g. `["male"]`, `["Austrian"]`,
`[]`), not as the CSV's single `"(Male)"`/`"(Austrian)"` text field the
original PRA1 notebook parsed with parenthesis regexes. `simplify_gender`
and `clean_nationalities` (renamed from `extract_nationalities`) below
operate on lists accordingly — confirmed by loading the real
`data/raw/Artworks.json` and inspecting `df["Gender"].apply(type)` /
`df["Nationality"].apply(type)` before writing the tests.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_data.py`:

```python
import pandas as pd

from src import data


def test_classify_medium_matches_known_keywords():
    assert data.classify_medium("Oil on canvas") == "painting"
    assert data.classify_medium("Gelatin silver print") == "photography"
    assert data.classify_medium(None) == "unknown"
    assert data.classify_medium("Unrecognizable stuff") == "other"


def test_simplify_gender_handles_known_patterns():
    assert data.simplify_gender("(male)") == "male"
    assert data.simplify_gender("(female)") == "female"
    assert data.simplify_gender("(male) (female)") == "mixed"
    assert data.simplify_gender("()") == "unknown"
    assert data.simplify_gender(None) == "unknown"


def test_extract_nationalities_parses_parentheses():
    assert data.extract_nationalities("(American)") == ["American"]
    assert data.extract_nationalities("(American) (British)") == ["American", "British"]
    assert data.extract_nationalities(None) == []


def test_get_region_maps_known_and_unknown_nationalities():
    assert data.get_region("American") == "North America"
    assert data.get_region("French") == "Europe"
    assert data.get_region("Atlantean") == "unknown"


def test_classify_decade_extracts_earliest_year():
    assert data.classify_decade("1913") == ("1910s", 1913)
    assert data.classify_decade("1913-1914") == ("1910s", 1913)
    assert data.classify_decade(None) == ("unknown", None)
    assert data.classify_decade("n.d.") == ("unknown", None)


def test_clean_artworks_adds_expected_columns():
    df = pd.DataFrame({
        "Medium": ["Oil on canvas"],
        "Gender": ["(male)"],
        "Nationality": ["(American)"],
        "Date": ["1913"],
    })
    cleaned = data.clean_artworks(df)
    for column in [
        "Medium_category", "Gender_simple", "Nationality_list",
        "Region_list", "Decade", "Year_min",
    ]:
        assert column in cleaned.columns
    assert cleaned.loc[0, "Medium_category"] == "painting"
    assert cleaned.loc[0, "Decade"] == "1910s"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_data.py -v`
Expected: FAIL with `ModuleNotFoundError` or `AttributeError` (no `src/data.py` yet).

- [ ] **Step 3: Write `src/data.py`**

```python
import re

import pandas as pd

_MEDIUM_CATEGORIES = {
    "painting": ["oil", "acrylic", "watercolor", "tempera", "gouache", "fresco", "enamel", "paint", "color"],
    "drawing": ["pencil", "graphite", "charcoal", "ink", "pastel", "crayon", "chalk", "pen", "pasted", "paper", "drawing"],
    "printmaking": ["lithograph", "etching", "engraving", "woodcut", "screenprint", "serigraph", "aquatint", "mezzotint", "drypoint", "offset", "portfolio", "linoleum", "poster", "silkscreen", "print", "printed"],
    "photography": ["photograph", "gelatin silver", "c-print", "chromogenic", "digital image", "film", "silver", "albumen", "photogravure", "collotype"],
    "sculpture": ["bronze", "stone", "marble", "wood", "ceramic", "plaster", "resin", "metal", "wax", "plastic", "steel"],
    "installation": ["installation", "video art", "single-channel video", "video installation"],
    "electronic": ["digital art", "electronic", "programming", "video games", "graphic art software", "digital"],
    "film": ["animation", "stop motion", "puppet film", "live action", "cinematography", "video", "sound"],
    "literature": ["book", "letterpress", "writing", "vellum", "papyrus", "journal"],
    "ceramics": ["clay", "porcelain", "pottery", "terracotta", "tile", "bone china"],
    "performing arts": ["performance", "dance", "theatre", "re-enactment"],
}

_REGION_MAP = {
    "North America": ["American", "Canadian"],
    "Latin America": ["Mexican", "Argentine", "Brazilian", "Peruvian", "Chilean", "Cuban", "Colombian", "Venezuelan"],
    "Europe": ["French", "German", "British", "Spanish", "Italian", "Swiss", "Dutch", "Polish", "Austrian", "Irish", "Portuguese", "Czech", "Belgian", "Greek", "Hungarian", "Norwegian", "Swedish", "Finnish", "Danish", "English", "Scottish"],
    "Europe/Asia": ["Russian", "Turkish"],
    "Asia": ["Chinese", "Japanese", "Indian", "Korean", "Vietnamese", "Filipino", "Israeli", "Iranian"],
    "Africa": ["Egyptian", "South African", "Nigerian", "Moroccan"],
    "Oceania": ["Australian", "New Zealander"],
}

_DECADE_PATTERN = re.compile(r"[1-2][0-9]{3}")


def classify_medium(medium) -> str:
    """Bucket a raw Medium string into a coarse category.

    Refined from the category keyword list validated in the original PRA1
    notebook (Visualizacion_Datos_PRA1_Alejandro_Hernandez_Mairal-Copy1.ipynb).
    """
    if pd.isna(medium):
        return "unknown"
    m = medium.lower()
    for category, keywords in _MEDIUM_CATEGORIES.items():
        if any(keyword in m for keyword in keywords):
            return category
    return "other"


def simplify_gender(gender) -> str:
    """Collapse MoMA's free-text Gender field to male/female/mixed/unknown.

    Refined from the original PRA1 notebook's simplify_gender().
    """
    if pd.isna(gender) or gender.strip() in ("", "()"):
        return "unknown"
    g = gender.lower()
    males = len(re.findall(r"\(male\)", g))
    females = len(re.findall(r"\(female\)", g))
    if males > 0 and females == 0:
        return "male"
    if females > 0 and males == 0:
        return "female"
    if males > 0 and females > 0:
        return "mixed"
    return "unknown"


def extract_nationalities(nationality) -> list:
    """Pull each parenthesized nationality out of MoMA's Nationality field."""
    if pd.isna(nationality):
        return []
    return re.findall(r"\((.*?)\)", str(nationality))


def get_region(nationality: str) -> str:
    """Map a single nationality string to a coarse world region."""
    for region, countries in _REGION_MAP.items():
        if nationality in countries:
            return region
    return "unknown"


def classify_decade(date):
    """Extract the earliest 4-digit year found in a free-text Date field
    and bucket it into a decade string, e.g. "1910s"."""
    if pd.isna(date) or str(date).strip() == "":
        return "unknown", None
    years = [int(y) for y in _DECADE_PATTERN.findall(str(date))]
    if not years:
        return "unknown", None
    year = min(years)
    decade = f"{(year // 10) * 10}s"
    return decade, year


def clean_artworks(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all categorization functions to a raw Artworks dataframe."""
    df = df.copy()
    df["Medium_category"] = df["Medium"].apply(classify_medium)
    df["Gender_simple"] = df["Gender"].apply(simplify_gender)
    df["Nationality_list"] = df["Nationality"].apply(extract_nationalities)
    df["Region_list"] = df["Nationality_list"].apply(
        lambda names: [get_region(n.strip()) for n in names] if names else ["unknown"]
    )
    df[["Decade", "Year_min"]] = df["Date"].apply(
        lambda d: pd.Series(classify_decade(d))
    )
    return df
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_data.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/data.py tests/test_data.py
git commit -m "feat: add MoMA data cleaning/categorization functions"
```

---

### Task 3: Raw data loading, downloading, and the EDA notebook

**Files:**
- Modify: `src/data.py` (add `download_raw_data`, `load_raw_data`, `save_processed`)
- Create: `notebooks/01_eda.ipynb`

**Interfaces:**
- Consumes: `config.DATA_RAW_DIR`, `config.DATA_PROCESSED_DIR`, `config.MOMA_ARTWORKS_URL`, `config.MOMA_ARTISTS_URL` (Task 1); `data.clean_artworks` (Task 2)
- Produces: `data.download_raw_data() -> None`, `data.load_raw_data() -> pd.DataFrame`, `data.save_processed(df: pd.DataFrame) -> Path` — consumed by `build_site.py` (Task 12) and the CI workflow (Task 13)

- [ ] **Step 1: Add the loader/downloader/saver functions to `src/data.py`**

Update the top of `src/data.py` (the existing `import re` / `import pandas as pd` lines from Task 2) to:

```python
import re
import urllib.request
from pathlib import Path

import pandas as pd

from . import config
```

Then add these three functions anywhere below `clean_artworks`:

```python
def download_raw_data() -> None:
    """Fetch fresh copies of Artworks.json/Artists.json from MoMA's GitHub repo."""
    config.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(config.MOMA_ARTWORKS_URL, config.DATA_RAW_DIR / "Artworks.json")
    urllib.request.urlretrieve(config.MOMA_ARTISTS_URL, config.DATA_RAW_DIR / "Artists.json")


def load_raw_data() -> pd.DataFrame:
    """Load whatever Artworks.json is currently in data/raw/."""
    return pd.read_json(config.DATA_RAW_DIR / "Artworks.json")


def save_processed(df: pd.DataFrame) -> Path:
    config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.DATA_PROCESSED_DIR / "artworks_clean.parquet"
    df.to_parquet(out_path)
    return out_path
```

- [ ] **Step 2: Manually verify against the real dataset**

Run:
```bash
python -c "from src import data; df = data.load_raw_data(); cleaned = data.clean_artworks(df); print(cleaned.shape); print(cleaned['Medium_category'].value_counts()); print(cleaned['Decade'].value_counts().head())"
```
Expected: no exceptions; row count matches `Artworks.json` (~160k rows); `Medium_category` and `Decade` value counts look plausible (no single category swallowing everything, no all-"unknown" column).

- [ ] **Step 3: Create `notebooks/01_eda.ipynb`**

A notebook with these cells, in order:
1. `from src import data` and `df = data.load_raw_data()`
2. `df.shape`, `df.info()`, `df[["Title", "Artist", "Nationality", "Date", "Medium", "Department"]].head()`
3. `cleaned = data.clean_artworks(df)`
4. `cleaned["Medium_category"].value_counts()`, `cleaned["Gender_simple"].value_counts()`, `cleaned["Region_list"].explode().value_counts()`, `cleaned["Decade"].value_counts().sort_index()`
5. `data.save_processed(cleaned)`

Run every cell top to bottom before committing; a notebook with stale/unexecuted output is not an acceptable deliverable.

- [ ] **Step 4: Commit**

```bash
git add src/data.py notebooks/01_eda.ipynb
git commit -m "feat: add raw data loading/downloading and EDA notebook"
```

---

### Task 4: Mondrian treemap chart

**Files:**
- Create: `src/charts.py`
- Test: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["mondrian"]` (Task 1); a cleaned dataframe with `Department` and `Medium_category` columns (Task 2)
- Produces: `charts.mondrian_treemap(df: pd.DataFrame) -> plotly.graph_objects.Figure` — consumed by `build_site.py` (Task 12)

- [ ] **Step 1: Write the failing test**

Create `tests/test_charts.py`:

```python
import pandas as pd
import plotly.graph_objects as go

from src import charts


def _sample_df():
    return pd.DataFrame({
        "Department": ["Painting", "Painting", "Drawing", "Sculpture"],
        "Medium_category": ["painting", "painting", "drawing", "sculpture"],
        "Region_list": [["Europe"], ["North America"], ["Europe"], ["Asia"]],
        "Decade": ["1910s", "1920s", "1910s", "1930s"],
    })


def test_mondrian_treemap_returns_figure_with_data():
    fig = charts.mondrian_treemap(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py::test_mondrian_treemap_returns_figure_with_data -v`
Expected: FAIL with `ModuleNotFoundError` (no `src/charts.py` yet)

- [ ] **Step 3: Write `src/charts.py` with the Mondrian chart**

```python
import plotly.express as px

from . import config


def mondrian_treemap(df):
    """Treemap of artwork counts by Department/Medium_category, colored and
    bordered to evoke Mondrian's grid of primary-color blocks."""
    palette = config.PALETTES["mondrian"]
    counts = (
        df.groupby(["Department", "Medium_category"])
        .size()
        .reset_index(name="count")
    )
    color_sequence = [palette["red"], palette["blue"], palette["yellow"], palette["black"]]
    fig = px.treemap(
        counts,
        path=["Department", "Medium_category"],
        values="count",
        color="Department",
        color_discrete_sequence=color_sequence,
    )
    fig.update_traces(marker=dict(line=dict(color=palette["black"], width=3)))
    fig.update_layout(paper_bgcolor=palette["background"], margin=dict(t=20, l=0, r=0, b=0))
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py::test_mondrian_treemap_returns_figure_with_data -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: add Mondrian treemap chart"
```

---

### Task 5: Les Demoiselles d'Avignon radar chart

**Files:**
- Modify: `src/charts.py`
- Modify: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["demoiselles"]` (Task 1); a cleaned dataframe with `Department` and `Region_list` columns (Task 2); `_sample_df()` fixture (Task 4)
- Produces: `charts.demoiselles_radar(df: pd.DataFrame) -> plotly.graph_objects.Figure` — consumed by `build_site.py` (Task 12)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_charts.py`:

```python
def test_demoiselles_radar_returns_figure_with_traces():
    fig = charts.demoiselles_radar(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py::test_demoiselles_radar_returns_figure_with_traces -v`
Expected: FAIL with `AttributeError: module 'src.charts' has no attribute 'demoiselles_radar'`

- [ ] **Step 3: Add `demoiselles_radar` to `src/charts.py`**

```python
import plotly.graph_objects as go


def demoiselles_radar(df):
    """Overlapping, semi-transparent radar traces (one per region) across
    the top departments, evoking the fragmented cubist planes of the
    painting's 5 figures."""
    palette = config.PALETTES["demoiselles"]
    top_departments = df["Department"].value_counts().nlargest(5).index.tolist()
    exploded = df.explode("Region_list")
    top_regions = exploded["Region_list"].value_counts().nlargest(4).index.tolist()
    colors = [palette["terracotta"], palette["pink"], palette["cream"], palette["brown"]]

    fig = go.Figure()
    for region, color in zip(top_regions, colors):
        subset = exploded[exploded["Region_list"] == region]
        counts = subset["Department"].value_counts().reindex(top_departments, fill_value=0)
        fig.add_trace(
            go.Scatterpolar(
                r=counts.values,
                theta=top_departments,
                fill="toself",
                name=region,
                opacity=0.55,
                line=dict(color=color),
                fillcolor=color,
            )
        )
    fig.update_layout(polar=dict(bgcolor=palette["background"]), showlegend=True)
    return fig
```

(Add `import plotly.graph_objects as go` once at the top of `src/charts.py`, alongside the existing `import plotly.express as px`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py::test_demoiselles_radar_returns_figure_with_traces -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: add Les Demoiselles d'Avignon radar chart"
```

---

### Task 6: Dance I circular bar chart

**Files:**
- Modify: `src/charts.py`
- Modify: `tests/test_charts.py`

**Interfaces:**
- Consumes: `config.PALETTES["dance"]` (Task 1); a cleaned dataframe with a `Decade` column (Task 2); `_sample_df()` fixture (Task 4)
- Produces: `charts.dance_circular_bar(df: pd.DataFrame) -> plotly.graph_objects.Figure` — consumed by `build_site.py` (Task 12)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_charts.py`:

```python
def test_dance_circular_bar_returns_figure_with_data():
    fig = charts.dance_circular_bar(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data[0].r) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_charts.py::test_dance_circular_bar_returns_figure_with_data -v`
Expected: FAIL with `AttributeError: module 'src.charts' has no attribute 'dance_circular_bar'`

- [ ] **Step 3: Add `dance_circular_bar` to `src/charts.py`**

```python
def dance_circular_bar(df):
    """Ring of colored bars (one per decade), echoing the circle of 5
    dancers and Matisse's 3 flat colors."""
    palette = config.PALETTES["dance"]
    colors = [palette["orange"], palette["green"], palette["blue"]]
    counts = df["Decade"].value_counts().sort_index()
    counts = counts[counts.index != "unknown"]

    fig = go.Figure(
        go.Barpolar(
            r=counts.values,
            theta=counts.index,
            marker_color=[colors[i % len(colors)] for i in range(len(counts))],
            marker_line_color="white",
            marker_line_width=1,
            opacity=0.9,
        )
    )
    fig.update_layout(polar=dict(radialaxis=dict(showticklabels=False)))
    return fig
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_charts.py::test_dance_circular_bar_returns_figure_with_data -v`
Expected: PASS

- [ ] **Step 5: Run the full chart test file**

Run: `pytest tests/test_charts.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/charts.py tests/test_charts.py
git commit -m "feat: add Dance I circular bar chart"
```

---

### Task 7: Chart prototyping notebook (qualitative gate)

**Files:**
- Create: `notebooks/02_chart_prototyping.ipynb`

**Interfaces:**
- Consumes: `data.load_raw_data`, `data.clean_artworks` (Task 3); `charts.mondrian_treemap`, `charts.demoiselles_radar`, `charts.dance_circular_bar` (Tasks 4-6)

This task has no pytest gate — per the spec, Pipeline A's check is qualitative (does the chart honestly represent the data, and does it read as the target painting?), done here before the charts are considered final.

- [ ] **Step 1: Create `notebooks/02_chart_prototyping.ipynb`**

Cells, in order:
1. `from src import data, charts` and load + clean the real dataset.
2. `charts.mondrian_treemap(cleaned).show()` — inspect: does the treemap read as a grid of red/blue/yellow/black blocks? Are the categories legible (not one giant dominant tile swallowing the rest)?
3. `charts.demoiselles_radar(cleaned).show()` — inspect: do the overlapping traces actually overlap and fragment, or does one trace dominate and hide the others? If one region's counts dwarf the rest, note it and consider a log scale or restricting to a comparable subset.
4. `charts.dance_circular_bar(cleaned).show()` — inspect: does the ring read cleanly with only 3 colors cycling, or does the color repetition (more decades than colors) become confusing? If confusing, note it as a candidate follow-up (e.g. group decades before the 1920s into "before").

- [ ] **Step 2: Record findings**

Add a Markdown cell at the end of the notebook stating, for each chart, whether it passed the qualitative check as-is, or what specific follow-up is needed. If a chart needs a follow-up (e.g. grouping sparse decades), do NOT silently fix it in this task — log it as a README Progress/Next-steps bullet (per the skill's negative-result-logging rule) and open a follow-up task instead of scope-creeping this one.

- [ ] **Step 3: Commit**

```bash
git add notebooks/02_chart_prototyping.ipynb
git commit -m "docs: validate the 3 chart functions against real MoMA data"
```

---

### Task 8: Geometrize reconstruction-error metric

**Files:**
- Create: `src/geometrize/evaluate.py`
- Test: `tests/test_geometrize_evaluate.py`

**Interfaces:**
- Produces: `evaluate.reconstruction_error(canvas: PIL.Image.Image, target: PIL.Image.Image) -> float` (0.0 = identical, 1.0 = maximally different) — consumed by `shapes.py`-driven fitting in `engine.py` (Task 10)

RMSE was chosen over SSIM for v1: it's simpler, needs no extra dependency beyond Pillow/NumPy already in use, and is sufficient to drive the hill-climbing accept/reject decision (this is an experiment-selection decision the spec left open — record it here rather than leaving both options ambiguous).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_geometrize_evaluate.py`:

```python
import pytest
from PIL import Image, ImageDraw

from src.geometrize import evaluate


def test_identical_images_have_zero_error():
    img = Image.new("RGB", (10, 10), (100, 150, 200))
    assert evaluate.reconstruction_error(img, img) == pytest.approx(0.0)


def test_opposite_images_have_max_error():
    black = Image.new("RGB", (10, 10), (0, 0, 0))
    white = Image.new("RGB", (10, 10), (255, 255, 255))
    assert evaluate.reconstruction_error(black, white) == pytest.approx(1.0)


def test_partial_difference_scores_between_extremes():
    target = Image.new("RGB", (10, 10), (200, 200, 200))
    half = target.copy()
    draw = ImageDraw.Draw(half)
    draw.rectangle([(0, 0), (9, 4)], fill=(0, 0, 0))
    err = evaluate.reconstruction_error(half, target)
    assert 0.0 < err < 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_geometrize_evaluate.py -v`
Expected: FAIL with `ModuleNotFoundError` (no `src/geometrize/evaluate.py` yet)

- [ ] **Step 3: Write `src/geometrize/evaluate.py`**

```python
import numpy as np
from PIL import Image


def reconstruction_error(canvas: Image.Image, target: Image.Image) -> float:
    """RMSE between two same-size images, normalized to [0, 1].

    0.0 means pixel-identical; 1.0 means maximally different (e.g. pure
    black vs. pure white). Drives the accept/reject decision in the
    Geometrize hill-climbing engine (src/geometrize/engine.py).
    """
    canvas_arr = np.asarray(canvas.convert("RGB"), dtype=np.float64) / 255.0
    target_arr = np.asarray(target.convert("RGB"), dtype=np.float64) / 255.0
    return float(np.sqrt(np.mean((canvas_arr - target_arr) ** 2)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_geometrize_evaluate.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/geometrize/evaluate.py tests/test_geometrize_evaluate.py
git commit -m "feat: add Geometrize reconstruction-error metric"
```

---

### Task 9: Geometrize shape representation, rendering, and SVG export

**Files:**
- Create: `src/geometrize/shapes.py`
- Test: `tests/test_geometrize_shapes.py`

**Interfaces:**
- Produces:
  - `shapes.Shape` (dataclass: `kind: str`, `points: list[tuple[int, int]]`, `color: tuple[int, int, int]`, `alpha: int`)
  - `shapes.random_shape(kind: str, target: PIL.Image.Image, rng: random.Random) -> Shape`
  - `shapes.mutate(shape: Shape, rng: random.Random, jitter: int = 10) -> Shape`
  - `shapes.render(canvas: PIL.Image.Image, shape: Shape) -> PIL.Image.Image`
  - `shapes.to_svg(shapes_list: list[Shape], size: tuple[int, int], background: tuple[int, int, int]) -> str`
  - all consumed by `engine.py` (Task 10) and `build_site.py` (Task 12)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_geometrize_shapes.py`:

```python
import random

from PIL import Image

from src.geometrize import shapes


def test_random_shape_stays_within_image_bounds():
    target = Image.new("RGB", (50, 50), (255, 0, 0))
    rng = random.Random(1)
    shape = shapes.random_shape("rectangle", target, rng)
    xs = [p[0] for p in shape.points]
    ys = [p[1] for p in shape.points]
    assert all(0 <= x < 50 for x in xs)
    assert all(0 <= y < 50 for y in ys)
    assert shape.kind == "rectangle"


def test_mutate_changes_points_but_keeps_kind_and_color():
    target = Image.new("RGB", (50, 50), (255, 0, 0))
    rng = random.Random(1)
    shape = shapes.random_shape("ellipse", target, rng)
    mutated = shapes.mutate(shape, rng)
    assert mutated.kind == shape.kind
    assert mutated.color == shape.color
    assert mutated.points != shape.points


def test_render_returns_same_size_rgba_image():
    canvas = Image.new("RGBA", (20, 20), (255, 255, 255, 255))
    shape = shapes.Shape(kind="rectangle", points=[(2, 2), (10, 10)], color=(255, 0, 0), alpha=128)
    result = shapes.render(canvas, shape)
    assert result.size == (20, 20)
    assert result.mode == "RGBA"


def test_to_svg_includes_one_element_per_shape():
    shape_list = [
        shapes.Shape(kind="rectangle", points=[(0, 0), (5, 5)], color=(255, 0, 0), alpha=255),
        shapes.Shape(kind="ellipse", points=[(1, 1), (4, 4)], color=(0, 255, 0), alpha=255),
        shapes.Shape(kind="triangle", points=[(0, 0), (5, 0), (2, 5)], color=(0, 0, 255), alpha=255),
    ]
    svg = shapes.to_svg(shape_list, size=(10, 10), background=(240, 240, 240))
    assert svg.count("<rect") == 2  # 1 background rect + 1 shape rect
    assert svg.count("<ellipse") == 1
    assert svg.count("<polygon") == 1
    assert svg.startswith("<svg")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_geometrize_shapes.py -v`
Expected: FAIL with `ModuleNotFoundError` (no `src/geometrize/shapes.py` yet)

- [ ] **Step 3: Write `src/geometrize/shapes.py`**

```python
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw


@dataclass
class Shape:
    kind: str  # "rectangle" | "triangle" | "ellipse"
    points: list
    color: tuple
    alpha: int  # 0-255


def random_shape(kind: str, target: Image.Image, rng: random.Random) -> Shape:
    """Sample a random shape whose bounding points stay within the target
    image, with its color drawn from the target's pixel at its centroid
    (matching Geometrize/primitive's color-sampling approach)."""
    w, h = target.size
    x0, y0 = rng.randint(0, w - 1), rng.randint(0, h - 1)
    size = max(2, min(w, h) // 6)
    x1 = min(w - 1, max(0, x0 + rng.randint(-size, size)))
    y1 = min(h - 1, max(0, y0 + rng.randint(-size, size)))

    if kind == "triangle":
        x2 = min(w - 1, max(0, x0 + rng.randint(-size, size)))
        y2 = min(h - 1, max(0, y0 + rng.randint(-size, size)))
        points = [(x0, y0), (x1, y1), (x2, y2)]
    else:
        points = [(min(x0, x1), min(y0, y1)), (max(x0, x1), max(y0, y1))]

    cx = min(w - 1, max(0, sum(p[0] for p in points) // len(points)))
    cy = min(h - 1, max(0, sum(p[1] for p in points) // len(points)))
    color = target.convert("RGB").getpixel((cx, cy))
    alpha = rng.randint(80, 180)
    return Shape(kind=kind, points=points, color=color, alpha=alpha)


def mutate(shape: Shape, rng: random.Random, jitter: int = 10) -> Shape:
    """Nudge each point of a shape by a small random offset (the
    hill-climbing refinement step)."""
    new_points = [
        (p[0] + rng.randint(-jitter, jitter), p[1] + rng.randint(-jitter, jitter))
        for p in shape.points
    ]
    return Shape(kind=shape.kind, points=new_points, color=shape.color, alpha=shape.alpha)


def render(canvas: Image.Image, shape: Shape) -> Image.Image:
    """Alpha-composite one shape on top of a copy of canvas."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fill = (*shape.color, shape.alpha)
    if shape.kind == "rectangle":
        draw.rectangle(shape.points, fill=fill)
    elif shape.kind == "ellipse":
        draw.ellipse(shape.points, fill=fill)
    elif shape.kind == "triangle":
        draw.polygon(shape.points, fill=fill)
    else:
        raise ValueError(f"unknown shape kind: {shape.kind}")
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


def to_svg(shapes_list, size, background) -> str:
    """Render placed shapes as a standalone SVG string."""
    width, height = size
    bg = f"rgb({background[0]},{background[1]},{background[2]})"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{bg}"/>',
    ]
    for shape in shapes_list:
        fill = f"rgb({shape.color[0]},{shape.color[1]},{shape.color[2]})"
        opacity = round(shape.alpha / 255, 3)
        if shape.kind == "rectangle":
            (x0, y0), (x1, y1) = shape.points
            parts.append(
                f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" '
                f'fill="{fill}" fill-opacity="{opacity}"/>'
            )
        elif shape.kind == "ellipse":
            (x0, y0), (x1, y1) = shape.points
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = abs(x1 - x0) / 2, abs(y1 - y0) / 2
            parts.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                f'fill="{fill}" fill-opacity="{opacity}"/>'
            )
        elif shape.kind == "triangle":
            pts = " ".join(f"{x},{y}" for x, y in shape.points)
            parts.append(f'<polygon points="{pts}" fill="{fill}" fill-opacity="{opacity}"/>')
    parts.append("</svg>")
    return "\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_geometrize_shapes.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/geometrize/shapes.py tests/test_geometrize_shapes.py
git commit -m "feat: add Geometrize shape representation, rendering, and SVG export"
```

---

### Task 10: Geometrize hill-climbing engine

**Files:**
- Create: `src/geometrize/engine.py`
- Test: `tests/test_geometrize_engine.py`

**Interfaces:**
- Consumes: `shapes.Shape/random_shape/mutate/render` (Task 9), `evaluate.reconstruction_error` (Task 8)
- Produces: `engine.GeometrizeResult` (dataclass: `canvas: PIL.Image.Image`, `shapes: list[Shape]`, `error_history: list[float]`), `engine.run(target: PIL.Image.Image, shape_kind: str, n_shapes: int, n_candidates: int = 50, n_refine: int = 20, seed: int = 42) -> GeometrizeResult` — consumed by `build_site.py` (Task 12)

- [ ] **Step 1: Write the failing test**

Create `tests/test_geometrize_engine.py`:

```python
from PIL import Image, ImageDraw

from src.geometrize import engine


def test_error_decreases_monotonically_over_iterations():
    target = Image.new("RGB", (20, 20), (255, 0, 0))
    draw = ImageDraw.Draw(target)
    draw.rectangle([(10, 0), (19, 19)], fill=(0, 0, 255))

    result = engine.run(
        target, shape_kind="rectangle", n_shapes=5,
        n_candidates=30, n_refine=10, seed=1,
    )

    assert len(result.error_history) >= 2
    assert result.error_history[-1] < result.error_history[0]
    assert all(
        result.error_history[i + 1] <= result.error_history[i]
        for i in range(len(result.error_history) - 1)
    )
    assert len(result.shapes) > 0
    assert result.canvas.size == target.size
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_geometrize_engine.py -v`
Expected: FAIL with `ModuleNotFoundError` (no `src/geometrize/engine.py` yet)

- [ ] **Step 3: Write `src/geometrize/engine.py`**

```python
import random
from dataclasses import dataclass

from PIL import Image

from . import evaluate
from . import shapes as shapes_mod


@dataclass
class GeometrizeResult:
    canvas: Image.Image
    shapes: list
    error_history: list


def run(target, shape_kind, n_shapes, n_candidates=50, n_refine=20, seed=42):
    """Hill-climbing shape placement: place n_shapes shapes one at a time,
    each chosen by sampling n_candidates random candidates, keeping the one
    that most reduces reconstruction error, then refining it for n_refine
    more mutation rounds. Mirrors Fogleman's `primitive` algorithm
    (see RESOURCES.md)."""
    rng = random.Random(seed)
    canvas = Image.new("RGBA", target.size, _average_color(target))
    placed_shapes = []
    error_history = [evaluate.reconstruction_error(canvas, target)]

    for _ in range(n_shapes):
        best_shape, best_score = _fit_one_shape(
            target, canvas, shape_kind, rng, n_candidates, n_refine, error_history[-1]
        )
        if best_shape is None:
            break
        canvas = shapes_mod.render(canvas, best_shape)
        placed_shapes.append(best_shape)
        error_history.append(best_score)

    return GeometrizeResult(canvas=canvas, shapes=placed_shapes, error_history=error_history)


def _fit_one_shape(target, canvas, shape_kind, rng, n_candidates, n_refine, current_score):
    best_shape = None
    best_score = current_score

    for _ in range(n_candidates):
        candidate = shapes_mod.random_shape(shape_kind, target, rng)
        candidate_canvas = shapes_mod.render(canvas, candidate)
        score = evaluate.reconstruction_error(candidate_canvas, target)
        if score < best_score:
            best_score = score
            best_shape = candidate

    if best_shape is None:
        return None, current_score

    for _ in range(n_refine):
        mutated = shapes_mod.mutate(best_shape, rng)
        mutated_canvas = shapes_mod.render(canvas, mutated)
        score = evaluate.reconstruction_error(mutated_canvas, target)
        if score < best_score:
            best_shape = mutated
            best_score = score

    return best_shape, best_score


def _average_color(image):
    r, g, b = image.convert("RGB").resize((1, 1)).getpixel((0, 0))
    return (r, g, b, 255)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_geometrize_engine.py -v`
Expected: PASS. This test does real work (150 candidate evaluations for 5 shapes) but on a 20x20 image, so it should complete in well under a second.

- [ ] **Step 5: Run the entire test suite**

Run: `pytest -v`
Expected: PASS (all tests from Tasks 2, 4-6, 8-10)

- [ ] **Step 6: Commit**

```bash
git add src/geometrize/engine.py tests/test_geometrize_engine.py
git commit -m "feat: add Geometrize hill-climbing engine"
```

---

### Task 11: Geometrize prototyping notebook — tune per-painting configs

**Files:**
- Create: `notebooks/03_geometrize_prototyping.ipynb`
- Modify: `src/config.py` (only if tuning changes the defaults in `GEOMETRIZE_CONFIGS`)

**Interfaces:**
- Consumes: `engine.run` (Task 10), `shapes.to_svg` (Task 9), `config.GEOMETRIZE_CONFIGS` (Task 1)

This is the notebook-validation step from `structuring-ml-projects`: try the engine on the 3 real painting images, look at the reconstruction-error curve and the visual result, and only then decide the per-painting defaults that graduate into `config.py`.

- [ ] **Step 1: Create `notebooks/03_geometrize_prototyping.ipynb`**

Cells, in order, repeated for each of `mondrian` / `demoiselles` / `dance`:
1. `from PIL import Image; from src import config; from src.geometrize import engine, shapes` and `target = Image.open(config.GEOMETRIZE_CONFIGS["mondrian"]["image"]).convert("RGB")`
2. Run the engine with the current config: `result = engine.run(target, shape_kind=config.GEOMETRIZE_CONFIGS["mondrian"]["shape_kind"], n_shapes=config.GEOMETRIZE_CONFIGS["mondrian"]["n_shapes"], n_candidates=..., n_refine=..., seed=config.RANDOM_STATE)`
3. Plot `result.error_history` (a simple `matplotlib` or `plotly` line chart) — confirm it's monotonically non-increasing and has visibly flattened by the last shape (if it's still dropping steeply, `n_shapes` is too low).
4. Display `result.canvas` — visually compare against the original image side by side.
5. If the result looks under-detailed or the error curve hasn't flattened, try a higher `n_shapes` (or more `n_candidates` for finer per-shape search) and re-run steps 2-4, holding everything else constant per the skill's before/after discipline.

- [ ] **Step 2: Update `config.py` only with configs that won**

For each painting, if a different `n_shapes`/`n_candidates`/`n_refine` produced a visibly better result at a comparable runtime, update that painting's entry in `config.GEOMETRIZE_CONFIGS` (Task 1) to the new values. If the original defaults from Task 1 already looked good, leave them and note that in the notebook instead of changing anything.

- [ ] **Step 3: Generate and save the final SVGs**

```python
from pathlib import Path

for painting, cfg in config.GEOMETRIZE_CONFIGS.items():
    target = Image.open(cfg["image"]).convert("RGB")
    result = engine.run(
        target, shape_kind=cfg["shape_kind"], n_shapes=cfg["n_shapes"],
        n_candidates=cfg["n_candidates"], n_refine=cfg["n_refine"],
        seed=config.RANDOM_STATE,
    )
    svg = shapes.to_svg(result.shapes, target.size, background=(240, 240, 240))
    out_path = config.OUTPUTS_DIR / "geometrize" / f"{painting}.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
```

- [ ] **Step 4: Commit**

```bash
git add notebooks/03_geometrize_prototyping.ipynb src/config.py
git commit -m "docs: tune Geometrize configs per painting and cache final SVGs"
```

(`outputs/` is gitignored per Task 1 — the SVGs are regenerated by `build_site.py`, Task 12, which caches them at the same path; this commit only needs to capture config changes and the notebook.)

---

### Task 12: Static site assembly (`build_site.py`)

**Files:**
- Create: `src/build_site.py`
- Test: `tests/test_build_site.py`

**Interfaces:**
- Consumes: `data.load_raw_data`, `data.clean_artworks` (Task 3); `charts.mondrian_treemap/demoiselles_radar/dance_circular_bar` (Tasks 4-6); `config.GEOMETRIZE_CONFIGS`, `config.OUTPUTS_DIR`, `config.RANDOM_STATE` (Task 1); `engine.run` (Task 10); `shapes.to_svg` (Task 9)
- Produces: `build_site.build_triptych_html(painting: str, chart_html: str, svg: str, image_rel_path: str) -> str`, `build_site.build_geometrize_svg(painting: str, force: bool = False) -> str`, `build_site.build_site(force_geometrize: bool = False) -> Path` (writes and returns `outputs/site/index.html`)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_build_site.py`:

```python
import pandas as pd
from PIL import Image

from src import build_site, config


def test_build_triptych_html_contains_expected_sections():
    html = build_site.build_triptych_html(
        "mondrian", "<div>chart</div>", "<svg></svg>", "../../images/x.jpg"
    )
    assert "Mondrian" in html
    assert "<div>chart</div>" in html
    assert "<svg></svg>" in html
    assert "Original" in html


def test_build_site_writes_index_html(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path / "outputs")

    tiny_image = tmp_path / "tiny.jpg"
    Image.new("RGB", (16, 16), (200, 50, 50)).save(tiny_image)
    for painting_cfg in config.GEOMETRIZE_CONFIGS.values():
        painting_cfg["image"] = tiny_image
        painting_cfg["n_shapes"] = 3
        painting_cfg["n_candidates"] = 5
        painting_cfg["n_refine"] = 2

    sample_df = pd.DataFrame({
        "Department": ["Painting"] * 4,
        "Medium_category": ["painting"] * 4,
        "Region_list": [["Europe"]] * 4,
        "Decade": ["1910s", "1920s", "1910s", "1930s"],
    })
    monkeypatch.setattr(build_site.data, "load_raw_data", lambda: sample_df)
    monkeypatch.setattr(build_site.data, "clean_artworks", lambda df: df)

    out_path = build_site.build_site()

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "MoMA Data Art" in content
    assert "Mondrian" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_build_site.py -v`
Expected: FAIL with `ModuleNotFoundError` (no `src/build_site.py` yet)

- [ ] **Step 3: Write `src/build_site.py`**

```python
from PIL import Image
import plotly.io as pio

from . import config, data, charts
from .geometrize import engine, shapes as shapes_mod

PAINTINGS = ["mondrian", "demoiselles", "dance"]

CHART_FUNCTIONS = {
    "mondrian": charts.mondrian_treemap,
    "demoiselles": charts.demoiselles_radar,
    "dance": charts.dance_circular_bar,
}


def build_geometrize_svg(painting: str, force: bool = False) -> str:
    svg_path = config.OUTPUTS_DIR / "geometrize" / f"{painting}.svg"
    if svg_path.exists() and not force:
        return svg_path.read_text(encoding="utf-8")

    cfg = config.GEOMETRIZE_CONFIGS[painting]
    target = Image.open(cfg["image"]).convert("RGB")
    result = engine.run(
        target,
        shape_kind=cfg["shape_kind"],
        n_shapes=cfg["n_shapes"],
        n_candidates=cfg["n_candidates"],
        n_refine=cfg["n_refine"],
        seed=config.RANDOM_STATE,
    )
    svg = shapes_mod.to_svg(result.shapes, target.size, background=(240, 240, 240))
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg, encoding="utf-8")
    return svg


def build_triptych_html(painting: str, chart_html: str, svg: str, image_rel_path: str) -> str:
    return f"""
    <section class="triptych">
      <h2>{painting.title()}</h2>
      <div class="triptych-row">
        <figure><img src="{image_rel_path}" alt="{painting} original"/><figcaption>Original</figcaption></figure>
        <figure>{chart_html}<figcaption>Data-driven chart</figcaption></figure>
        <figure>{svg}<figcaption>Geometrize recreation</figcaption></figure>
      </div>
    </section>
    """


def build_site(force_geometrize: bool = False):
    df = data.clean_artworks(data.load_raw_data())
    sections = []
    for painting in PAINTINGS:
        chart_fig = CHART_FUNCTIONS[painting](df)
        chart_html = pio.to_html(chart_fig, include_plotlyjs="cdn", full_html=False)
        svg = build_geometrize_svg(painting, force=force_geometrize)
        image_name = config.GEOMETRIZE_CONFIGS[painting]["image"].name
        image_rel_path = f"../../images/{image_name}"
        sections.append(build_triptych_html(painting, chart_html, svg, image_rel_path))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>MoMA Data Art</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    .triptych-row {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
    .triptych-row figure {{ flex: 1; min-width: 280px; }}
    img, svg {{ max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <h1>MoMA Data Art</h1>
  {''.join(sections)}
</body>
</html>"""

    out_path = config.OUTPUTS_DIR / "site" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    build_site()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_build_site.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the entire test suite**

Run: `pytest -v`
Expected: PASS (every test from Tasks 2, 4-6, 8-10, 12)

- [ ] **Step 6: Manually build the real site**

Run: `python -m src.build_site`
Expected: no exceptions; `outputs/site/index.html` exists; open it in a browser and confirm all 3 triptychs render (original image, Plotly chart, Geometrize SVG) without broken images or empty sections.

- [ ] **Step 7: Commit**

```bash
git add src/build_site.py tests/test_build_site.py
git commit -m "feat: assemble static site with data charts and Geometrize recreations"
```

---

### Task 13: Scheduled GitHub Actions data refresh

**Files:**
- Create: `.github/workflows/refresh-data.yml`

**Interfaces:**
- Consumes: `data.download_raw_data` (Task 3), `build_site.build_site` (Task 12)

- [ ] **Step 1: Write `.github/workflows/refresh-data.yml`**

```yaml
name: Refresh MoMA data

on:
  schedule:
    - cron: "0 6 * * 1"  # every Monday at 06:00 UTC
  workflow_dispatch: {}

jobs:
  refresh:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Refresh data and rebuild the site
        run: |
          python -c "from src import data; data.download_raw_data()"
          python -m src.build_site

      - name: Commit changes if any
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -f outputs/site outputs/charts
          git diff --cached --quiet || git commit -m "chore: scheduled MoMA data refresh"
          git push
```

Note: `outputs/` and `data/raw/` are both gitignored (Task 1) — `Artworks.json` alone is
~137MB, over GitHub's 100MB per-file push limit, so raw data must never be committed,
only downloaded fresh each run via `download_raw_data()`. The deployed site still needs
`outputs/site/` tracked, so this step's `git add -f` deliberately overrides the ignore
rule for `outputs/site` and `outputs/charts` only — `data/raw` is never added, in CI or
locally.

- [ ] **Step 2: Validate the workflow syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/refresh-data.yml'))"` (requires `pyyaml`; if not installed, visually re-check indentation instead — this is a syntax check, not a full CI dry run, since GitHub Actions can't be executed locally).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/refresh-data.yml
git commit -m "ci: add scheduled MoMA data refresh workflow"
```

---

### Task 14: GitHub Pages setup and README finalization

**Files:**
- Modify: `README.md`
- Create/Modify: repository GitHub Pages settings (manual, not a file change)

**Interfaces:**
- Consumes: `outputs/site/index.html` (Task 12)

- [ ] **Step 1: Decide and document the Pages source**

Since `outputs/` is gitignored locally but committed by CI (Task 13), GitHub Pages should serve from the branch CI pushes to (default: the same branch, `outputs/site` as the Pages folder) or a dedicated `gh-pages` branch — pick one and record the choice in `README.md`'s Progress log. This step is a repository setting change (Settings → Pages in the GitHub UI) that needs your explicit action on GitHub itself; it is not something to script.

- [ ] **Step 2: Update `README.md`'s Progress and Next steps**

```markdown
## Progress

- [x] Project scaffolding
- [x] Data pipeline (src/data.py, tested)
- [x] Chart functions: Mondrian treemap, Demoiselles radar, Dance I circular bar
- [x] Geometrize engine (hill-climbing, RMSE-driven, tested)
- [x] Static site assembly (src/build_site.py)
- [x] Scheduled GitHub Actions data refresh
- [ ] Enable GitHub Pages in repo settings and record the resulting URL here

## Next steps

- [ ] Add Starry Night and Water Lilies (see spec's Extensibility section)
- [ ] Confirm the exact MoMA-catalogued title behind `images/mondrian_composition.jpg`
```

- [ ] **Step 3: Run the full test suite one last time**

Run: `pytest -v`
Expected: PASS (every test across the whole project)

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: finalize README progress log and next steps"
```
