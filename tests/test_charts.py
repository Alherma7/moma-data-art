import pandas as pd
import plotly.graph_objects as go

from src import charts, config


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


def test_mondrian_treemap_only_uses_the_four_palette_colors():
    # Locks in the coloring rule: every marker color used across the
    # treemap must be one of the 4 Mondrian palette colors (red/blue/
    # yellow/black) -- catches a regression back to some other coloring
    # scheme (e.g. a default continuous scale) going unnoticed.
    palette = config.PALETTES["mondrian"]
    fig = charts.mondrian_treemap(_sample_df())
    allowed = {palette["red"], palette["blue"], palette["yellow"], palette["black"]}
    assert set(fig.data[0].marker.colors) <= allowed


def test_demoiselles_voronoi_covers_every_decade():
    df = _sample_df()
    fig = charts.demoiselles_voronoi(df)
    assert isinstance(fig, go.Figure)
    decade_names_in_figure = {trace.name for trace in fig.data}
    assert decade_names_in_figure == set(df["Decade"].unique())


def test_demoiselles_voronoi_pools_sparse_decades_into_other():
    # A decade below 3% of the total count should be folded into "Other"
    # rather than getting its own cell (finding: sparse decades otherwise
    # get a disproportionately large area relative to their tiny share).
    n_common = 32  # each of 3 common decades: 32/100 = 32% share
    n_sparse = 2   # each of 2 sparse decades: 2/100 = 2% share (< 3%)
    df = pd.DataFrame({
        "Decade": (
            ["1920s"] * n_common + ["1930s"] * n_common + ["1940s"] * n_common
            + ["1900s"] * n_sparse + ["1910s"] * n_sparse
        ),
        "Gender_simple": ["male", "female"] * ((3 * n_common + 2 * n_sparse) // 2),
    })
    fig = charts.demoiselles_voronoi(df)
    trace_names = {trace.name for trace in fig.data}
    assert trace_names == {"1920s", "1930s", "1940s", "Other"}
    assert "1900s" not in trace_names
    assert "1910s" not in trace_names


def test_dance_scatter_returns_one_point_per_group_work_decade():
    df = _sample_df()
    fig = charts.dance_scatter(df)
    assert isinstance(fig, go.Figure)
    expected_decades = df[df["Num_participants"] >= 2]["Decade"].nunique()
    assert len(fig.data[0].x) == expected_decades
