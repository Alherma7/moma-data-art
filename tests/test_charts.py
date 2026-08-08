import pandas as pd
import plotly.graph_objects as go

from src import charts, config, data, demoiselles_geometry, mondrian_geometry


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
    assert "1960s" in largest_trace.text


def test_mondrian_treemap_unassigned_rectangles_have_empty_hover():
    df = pd.DataFrame({"Decade_acquired": ["1960s"]})
    fig = charts.mondrian_treemap(df)
    n_background = len(mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES)
    n_colored = len(mondrian_geometry.MONDRIAN_RECTANGLES)
    colored_traces = fig.data[2 * n_background: 2 * n_background + n_colored]
    empty_hover_traces = [t for t in colored_traces if t.hoverinfo == "skip"]
    assert len(empty_hover_traces) == n_colored - 1


def test_mondrian_treemap_labels_fill_hover_via_text_not_hovertemplate():
    """plotly.js forces ``hovertemplate: false`` for ``hoveron='fills'``
    hovers and labels them from the trace's scalar ``text`` instead, so a
    hovertemplate here would silently render as "trace N"."""
    df = pd.DataFrame({"Decade_acquired": ["1960s"] * 5 + ["1970s"] * 2})
    fig = charts.mondrian_treemap(df)
    n_background = len(mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES)
    n_colored = len(mondrian_geometry.MONDRIAN_RECTANGLES)
    colored_traces = fig.data[2 * n_background: 2 * n_background + n_colored]
    labelled = [t for t in colored_traces if t.hoverinfo == "text"]
    assert len(labelled) == 2
    for trace in labelled:
        assert trace.hovertemplate is None
        assert trace.hoveron == "fills"
        assert isinstance(trace.text, str)
        assert trace.name == ""


_DEMOISELLES_DF = data.clean_artworks(data.load_raw_data())


def test_demoiselles_voronoi_returns_figure():
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    assert isinstance(fig, go.Figure)


def test_demoiselles_voronoi_hover_never_contains_a_gender_word():
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    for trace in fig.data:
        if trace.hoverinfo == "text" and trace.text:
            assert "Woman" not in trace.text
            assert "Man" not in trace.text
            assert "Transgender" not in trace.text


def test_demoiselles_voronoi_legend_has_three_gender_entries_with_correct_colors():
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    legend_traces = [t for t in fig.data if t.showlegend]
    legend_names = {t.name for t in legend_traces}
    assert legend_names == {"Woman", "Man", "Transgender"}
    for trace in legend_traces:
        expected_color = config.PALETTES["demoiselles"][charts._GENDER_PALETTE_KEYS[trace.name]]
        assert trace.marker.color == expected_color


def test_demoiselles_voronoi_labels_fill_hover_via_text_not_hovertemplate():
    """Same plotly.js quirk as Mondrian's fill hovers -- see
    test_mondrian_treemap_labels_fill_hover_via_text_not_hovertemplate."""
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    for trace in fig.data:
        if trace.hoveron == "fills":
            assert trace.hovertemplate is None


def test_demoiselles_voronoi_top_ranked_cell_carries_the_top_ranked_category():
    """Cell index 0 in demoiselles_geometry.DEMOISELLES_CELLS is the
    category with the highest artwork count, by construction of ANCHORS
    (placed in CATEGORY_ITEMS rank order). When df is the same dataset
    the geometry was built from, index 0's hover text must match the
    top-ranked (decade, gender) pair."""
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    top_decade, top_gender = demoiselles_geometry.CATEGORY_ITEMS[0][0]
    first_cell_trace = fig.data[0]
    assert top_decade in first_cell_trace.text
    assert first_cell_trace.fillcolor == config.PALETTES["demoiselles"][charts._GENDER_PALETTE_KEYS[top_gender]]


def test_demoiselles_voronoi_has_no_flat_face_traces():
    """Faces are real image crops (fig.layout.images), not fill='toself'
    traces -- unlike the data cells, fig.data should contain nothing for
    the 5 faces."""
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    n_cells = len(demoiselles_geometry.DEMOISELLES_CELLS)
    n_legend = len(charts._GENDER_PALETTE_KEYS)
    trace_cell_counts = sum(
        len(cell.geoms) if cell.geom_type == "MultiPolygon" else 1
        for cell in demoiselles_geometry.DEMOISELLES_CELLS.values()
    )
    assert len(fig.data) == trace_cell_counts + n_legend
    assert n_cells > 0


def test_demoiselles_voronoi_overlays_one_image_per_face():
    fig = charts.demoiselles_voronoi(_DEMOISELLES_DF)
    assert len(fig.layout.images) == len(demoiselles_geometry.FACE_CONTOURS)
    for image in fig.layout.images:
        assert image.source.startswith("data:image/png;base64,")
