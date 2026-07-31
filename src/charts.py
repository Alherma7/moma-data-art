import random

import plotly.express as px
import plotly.graph_objects as go

from . import config, voronoi_treemap


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
    planes. A decade's merged cell is usually one contiguous polygon but
    may legitimately come back as a few small fragments (MultiPolygon) —
    each fragment is rendered as its own trace sharing the decade's name,
    color, and legend entry."""
    palette = config.PALETTES["demoiselles"]
    known = df[df["Decade"] != "unknown"]
    weights = known["Decade"].value_counts().to_dict()

    rng = random.Random(config.RANDOM_STATE)
    points = voronoi_treemap.sample_points(weights, rng)
    cells = voronoi_treemap.voronoi_cells(points)

    fig = go.Figure()
    for decade, geometry in cells.items():
        subset = known[known["Decade"] == decade]
        male = (subset["Gender_simple"] == "male").sum()
        female = (subset["Gender_simple"] == "female").sum()
        ratio = male / (male + female) if (male + female) > 0 else 0.5
        color = _interpolate_hex(palette["pink"], palette["brown"], ratio)

        polygons = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        for i, polygon in enumerate(polygons):
            x, y = polygon.exterior.xy
            fig.add_trace(
                go.Scatter(
                    x=list(x),
                    y=list(y),
                    fill="toself",
                    fillcolor=color,
                    line=dict(color=palette["terracotta"], width=1),
                    name=decade,
                    legendgroup=decade,
                    showlegend=(i == 0),
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
