import pandas as pd
import plotly.graph_objects as go

from src import charts


def _sample_df():
    return pd.DataFrame({
        "Department": ["Painting", "Painting", "Drawing", "Sculpture"],
        "Medium_category": ["painting", "painting", "drawing", "sculpture"],
        "Region_list": [["Europe"], ["North America"], ["Europe"], ["Asia"]],
        "Decade": ["1910s", "1920s", "1910s", "1930s"],
    })


def test_mondrian_treemap_returns_figure_with_data():
    fig = charts.mondrian_treemap(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_demoiselles_radar_returns_figure_with_traces():
    fig = charts.demoiselles_radar(_sample_df())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
