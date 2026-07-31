import pandas as pd
import plotly.graph_objects as go

from src import charts


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


def test_demoiselles_voronoi_returns_one_trace_per_decade():
    df = _sample_df()
    fig = charts.demoiselles_voronoi(df)
    assert isinstance(fig, go.Figure)
    decade_names_in_figure = {trace.name for trace in fig.data}
    assert decade_names_in_figure == set(df["Decade"].unique())
