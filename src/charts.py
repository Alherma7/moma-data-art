import plotly.express as px
import plotly.graph_objects as go

from . import config


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
