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
