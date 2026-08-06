import pandas as pd
import plotly.graph_objects as go

from src import charts, mondrian_geometry


def test_assign_decades_exact_match_ranks_by_count():
    counts = {"1990s": 50, "1960s": 100, "2000s": 20}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("1960s", 100), ("1990s", 50), ("2000s", 20)]


def test_assign_decades_pools_smallest_into_other_when_too_many():
    counts = {"1960s": 100, "1970s": 80, "1980s": 10, "1990s": 5, "2000s": 3}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("1960s", 100), ("1970s", 80), ("Other", 18)]


def test_assign_decades_resorts_other_by_its_own_total():
    counts = {"1960s": 50, "1970s": 40, "1980s": 30, "1990s": 25, "2000s": 20}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("Other", 75), ("1960s", 50), ("1970s", 40)]


def test_assign_decades_leaves_leftover_rectangles_unassigned():
    counts = {"1960s": 100, "1970s": 80}
    result = charts._assign_decades_to_rectangles(counts, 4)
    assert result == [("1960s", 100), ("1970s", 80), None, None]


def test_mondrian_treemap_returns_expected_trace_count():
    df = pd.DataFrame({"Decade_acquired": ["1960s", "1970s", "1990s"]})
    fig = charts.mondrian_treemap(df)
    assert isinstance(fig, go.Figure)
    n_colored = len(mondrian_geometry.MONDRIAN_RECTANGLES)
    n_background = len(mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES)
    # 1 fill trace + 1 border trace per background rectangle, 1 trace per
    # colored rectangle, plus 1 shared trace for all decorative lines/ticks.
    assert len(fig.data) == n_colored + 2 * n_background + 1


def test_mondrian_treemap_assigns_most_acquired_decade_to_largest_rectangle():
    df = pd.DataFrame({"Decade_acquired": ["1960s"] * 5 + ["1970s"] * 2 + ["1990s"] * 1})
    fig = charts.mondrian_treemap(df)
    largest_rect = max(
        mondrian_geometry.MONDRIAN_RECTANGLES,
        key=lambda r: (r["x1"] - r["x0"]) * (r["y1"] - r["y0"]),
    )
    n_background = len(mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES)
    largest_trace = fig.data[2 * n_background]  # first colored-rectangle trace
    assert largest_trace.x[0] == largest_rect["x0"]
    assert "1960s" in largest_trace.hovertemplate


def test_mondrian_treemap_unassigned_rectangles_have_empty_hover():
    df = pd.DataFrame({"Decade_acquired": ["1960s"]})
    fig = charts.mondrian_treemap(df)
    n_background = len(mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES)
    n_colored = len(mondrian_geometry.MONDRIAN_RECTANGLES)
    colored_traces = fig.data[2 * n_background: 2 * n_background + n_colored]
    empty_hover_traces = [t for t in colored_traces if t.hovertemplate == "<extra></extra>"]
    assert len(empty_hover_traces) == n_colored - 1
