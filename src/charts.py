import plotly.graph_objects as go

from . import config, demoiselles_geometry, mondrian_geometry

GRID_LINE_WIDTH = 5


def _rectangle_trace(rect, palette, hovertext=None):
    """Rectangle outline + fill. Hover is driven by ``hoveron='fills'`` so
    the whole interior is hoverable, not just the corner vertices. Note
    that plotly.js *ignores* ``hovertemplate`` on a fill hover (it forces
    ``hovertemplate: false`` internally and falls back to the trace's
    scalar ``text``, or to the trace name if there is none -- which is
    why a hovertemplate here silently renders as "trace N"). So the label
    has to be passed as a scalar ``text`` with ``hoverinfo='text'``."""
    x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
    return go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        fill="toself",
        fillcolor=palette[rect["color"]],
        line=dict(color=palette["black"], width=GRID_LINE_WIDTH),
        mode="lines",
        hoveron="fills",
        name="",
        text=hovertext,
        hoverinfo="text" if hovertext else "skip",
        showlegend=False,
    )


def _fill_only_trace(rect, palette):
    x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
    return go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        fill="toself",
        fillcolor=palette[rect["color"]],
        line=dict(width=0),
        mode="lines",
        hoverinfo="skip",
        showlegend=False,
    )


def _segments_trace(segments, color, width=GRID_LINE_WIDTH):
    xs, ys = [], []
    for (sx0, sy0), (sx1, sy1) in segments:
        xs += [sx0, sx1, None]
        ys += [sy0, sy1, None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), hoverinfo="skip", showlegend=False)


def _assign_decades_to_rectangles(decade_counts, n_rectangles):
    """Rank decades by count descending and zip them to rectangle ranks
    (rectangles are assumed pre-sorted by area descending by the
    caller). If there are more decades than rectangles, the smallest
    decades are pooled into a single "Other" entry and the result is
    re-sorted (the pooled total can outrank individually-kept decades).
    If there are more rectangles than decades, the smallest-ranked
    rectangles are left unassigned (None)."""
    items = sorted(decade_counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(items) > n_rectangles:
        keep = items[: n_rectangles - 1]
        other_total = sum(count for _, count in items[n_rectangles - 1:])
        items = keep + [("Other", other_total)]
        items.sort(key=lambda kv: kv[1], reverse=True)
    assignments = list(items) + [None] * (n_rectangles - len(items))
    return assignments[:n_rectangles]


def mondrian_treemap(df):
    """Rectangles digitized from the reference Mondrian-style image
    (src/mondrian_geometry.py), rendered in their painted colors with
    the most-acquired decade assigned to the largest rectangle, ranked
    on down. Color is never a data encoding here -- only the hover text
    (decade + count) is. Background fill, open corners, and the
    decorative line overshoots/crosses all come from
    mondrian_geometry and are drawn as-is, independent of the data."""
    palette = config.PALETTES["mondrian"]
    known = df[df["Decade_acquired"] != "unknown"]
    decade_counts = known["Decade_acquired"].value_counts().to_dict()

    rectangles_sorted = sorted(
        mondrian_geometry.MONDRIAN_RECTANGLES,
        key=lambda r: (r["x1"] - r["x0"]) * (r["y1"] - r["y0"]),
        reverse=True,
    )
    assignments = _assign_decades_to_rectangles(decade_counts, len(rectangles_sorted))

    x_min = min(r["x0"] for r in mondrian_geometry.MONDRIAN_RECTANGLES)
    x_max = max(r["x1"] for r in mondrian_geometry.MONDRIAN_RECTANGLES)
    y_min = min(r["y0"] for r in mondrian_geometry.MONDRIAN_RECTANGLES)
    y_max = max(r["y1"] for r in mondrian_geometry.MONDRIAN_RECTANGLES)
    decorative_segments = [
        mondrian_geometry.line_segment(line)
        for line in mondrian_geometry.MONDRIAN_LINE_OVERSHOOTS + mondrian_geometry.MONDRIAN_CROSS_TICKS
    ]
    overshoot_xs = [p[0] for seg in decorative_segments for p in seg]
    overshoot_ys = [p[1] for seg in decorative_segments for p in seg]
    plot_x_min = min([x_min] + overshoot_xs)
    plot_x_max = max([x_max] + overshoot_xs)
    plot_y_min = min([y_min] + overshoot_ys)
    plot_y_max = max([y_max] + overshoot_ys)

    fig = go.Figure()
    for rect in mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES:
        fig.add_trace(_fill_only_trace(rect, palette))
        fig.add_trace(_segments_trace(
            mondrian_geometry.background_edge_segments(rect, mondrian_geometry.MONDRIAN_RECTANGLES),
            palette["black"],
        ))
    for rect, assignment in zip(rectangles_sorted, assignments):
        if assignment is not None:
            decade, count = assignment
            hovertext = f"{decade}<br>{count} artworks"
        else:
            hovertext = None
        fig.add_trace(_rectangle_trace(rect, palette, hovertext=hovertext))
    fig.add_trace(_segments_trace(decorative_segments, palette["black"]))

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[plot_x_min, plot_x_max]),
        yaxis=dict(visible=False, range=[plot_y_min, plot_y_max], scaleanchor="x"),
        showlegend=False,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig


def _polygon_traces(polygon, fillcolor, palette, hovertext=None):
    """Renders a shapely Polygon or MultiPolygon as one or more filled
    Plotly traces. Hover is driven by hoveron='fills' so the whole
    interior is hoverable; plotly.js ignores hovertemplate on fill
    hovers, so the label must be a scalar text with hoverinfo='text' (see
    _rectangle_trace above)."""
    geoms = polygon.geoms if polygon.geom_type == "MultiPolygon" else [polygon]
    traces = []
    for geom in geoms:
        xs, ys = geom.exterior.xy
        traces.append(go.Scatter(
            x=list(xs), y=list(ys),
            fill="toself", fillcolor=fillcolor,
            line=dict(color=palette["black"], width=2),
            mode="lines", hoveron="fills", name="",
            text=hovertext, hoverinfo="text" if hovertext else "skip",
            showlegend=False,
        ))
    return traces


_GENDER_PALETTE_KEYS = {"Mujer": "mujer", "Hombre": "hombre", "Transgénero": "transgenero"}


def _legend_proxy_traces(palette):
    """Invisible marker traces used only to produce legend entries --
    Plotly doesn't auto-generate a legend for fill='toself' traces."""
    return [
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=palette[palette_key]),
            name=label, showlegend=True,
        )
        for label, palette_key in _GENDER_PALETTE_KEYS.items()
    ]


def demoiselles_voronoi(df):
    """Voronoi cells tessellated over images/les_demoiselles_davignon.png
    (src/demoiselles_geometry.py): a weighted (power) Voronoi diagram
    whose cell area is fit to each (decade, gender) category's artwork
    count, then clipped against the 5 fixed face contours so faces stay
    undivided decoration. Unlike mondrian_treemap, color IS a data
    encoding here -- a cell's fill color is the gender of its assigned
    category. Cell geometry is fixed at import time
    (demoiselles_geometry.DEMOISELLES_CELLS, solved against the full
    cleaned dataset); df only re-ranks categories for the assignment and
    hover text, so it should normally be the same dataset the geometry
    was built from. Hover shows decade + count only -- gender is already
    shown via color and the legend."""
    palette = config.PALETTES["demoiselles"]
    df_items = demoiselles_geometry.category_items(df)

    fig = go.Figure()
    for face in demoiselles_geometry.FACE_POLYGONS:
        for trace in _polygon_traces(face, palette["face"], palette):
            fig.add_trace(trace)

    for i, cell in demoiselles_geometry.DEMOISELLES_CELLS.items():
        if i >= len(df_items):
            continue
        (decade, gender), count = df_items[i]
        fillcolor = palette[_GENDER_PALETTE_KEYS[gender]]
        hovertext = f"{decade}<br>{count} obras"
        for trace in _polygon_traces(cell, fillcolor, palette, hovertext=hovertext):
            fig.add_trace(trace)

    for trace in _legend_proxy_traces(palette):
        fig.add_trace(trace)

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
        showlegend=True,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig
