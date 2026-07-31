import random

import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

from . import config, voronoi_treemap


def mondrian_treemap(df):
    """Treemap of artwork counts by acquisition decade and credit category,
    colored to evoke Mondrian's grid of primary-color blocks: the 5
    most-acquired decades, sorted chronologically; the earliest 3 of those
    5 get red/blue/yellow, the rest (including every decade outside the
    top 5) get black."""
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
    """Voronoi treemap with one cell per decade (decades below 3% of total
    count are pooled into a single "Other" cell, to avoid the area-encoding
    distortion sparse decades cause otherwise), sized by artwork count and
    colored by gender ratio (pale pink = balanced/female-leaning, dark
    maroon = male-dominated), evoking the painting's fragmented cubist
    planes. A decade's merged cell is usually one contiguous polygon but
    may legitimately come back as a few small fragments (MultiPolygon) —
    each fragment is rendered as its own trace sharing the decade's name,
    color, and legend entry."""
    palette = config.PALETTES["demoiselles"]
    known = df[df["Decade"] != "unknown"].copy()
    if known.empty:
        return go.Figure()

    decade_counts = known["Decade"].value_counts()
    total_count = decade_counts.sum()
    small_decades = decade_counts[decade_counts / total_count < 0.03].index
    known["Decade_grouped"] = known["Decade"].where(
        ~known["Decade"].isin(small_decades), "Other"
    )

    weights = known["Decade_grouped"].value_counts().to_dict()

    rng = random.Random(config.RANDOM_STATE)
    points = voronoi_treemap.sample_points(weights, rng)
    cells = voronoi_treemap.voronoi_cells(points)

    fig = go.Figure()
    for group, geometry in cells.items():
        subset = known[known["Decade_grouped"] == group]
        male = (subset["Gender_simple"] == "male").sum()
        female = (subset["Gender_simple"] == "female").sum()
        if male + female == 0:
            color = palette["cream"]
        else:
            ratio = male / (male + female)
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
                    name=group,
                    legendgroup=group,
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
