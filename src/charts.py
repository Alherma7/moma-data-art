import plotly.express as px
import plotly.graph_objects as go

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
