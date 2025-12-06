import sys
import secrets
from pathlib import Path
from typing import Optional, Any

import polars as pl
import plotly.express as px
import streamlit as st
import plotly.graph_objs as go


def generate_secure_hex_color():
    return f"#{secrets.randbelow(256):02x}{secrets.randbelow(256):02x}{secrets.randbelow(256):02x}"


def error_handler(error_matches: Optional[dict[str, str]] = None, default: Any = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as err:
                print(err)
                return default
        return wrapper
    return decorator


def pth(path: str) -> Path:
    path_obj = Path(path).expanduser().absolute()

    if not path_obj.exists():
        raise FileNotFoundError(f"Not found path {path_obj}")

    return path_obj



def main():

    segments_path = pth("~/Projects/Data/new_COD/segments_config.csv")
    segments_df = pl.read_csv(str(segments_path))

    colors_id_path = pth("~/Projects/Data/new_COD/colors_by_id.csv")
    colors_id_df = pl.read_csv(str(colors_id_path))

    data_path = pth("~/Projects/Data/new_COD/data.csv")
    data_df_full = pl.read_csv(str(data_path))

    data_df_full = data_df_full.with_columns(
        pl.col("timestamp")
        .str.strptime(pl.Datetime, format="%Y:%m:%d %H-%M-%S")
        .alias("datetime")
    )

    # data_df = data_df.filter(pl.col("id") == "1")
    data_df = data_df_full.filter(pl.col("group") == "1")

    data_to_draw = {"time": [], "temp": []}
    available_dates = data_df.select("datetime").unique().sort("datetime")
    for row in available_dates.iter_rows():
        date = row[0]
        result = data_df.filter(pl.col("datetime") == date).select(["dist", "temp"])

        data_to_draw["time"].append(date)
        data_to_draw["temp"].append(result["temp"].max())

    df_draw = pl.DataFrame(data_to_draw)

    # fig = px.line(df_draw, x='time', y='temp', title='Temp by time')
    fig = px.histogram(data_df_full, x="datetime")

    fig.update_layout(
        width=1800,
        height=800,
        hovermode='closest'
    )

    st.plotly_chart(fig, width="content")

    sys.exit(0)

    test_path_1 = "~/Projects/Data/COD/COD_data/00000000000050FE/therm_ch01_2025-09-21_01-26-09_i0000000000029C13.csv"
    test_path_2 = "~/Projects/Data/COD/COD_data/00000000000050FE/therm_ch01_2025-09-21_01-26-39_i0000000000029C14.csv"

    df1 = open_df(test_path_1)
    df2 = open_df(test_path_2)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df1["dist"],
        y=df1["temp"],
        mode='lines',
        line=dict(color='red'),
        name='Line 1',
        hovertemplate='dist: %{x}<br>temp: %{y}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df2["dist"],
        y=df2["temp"],
        mode='lines',
        line=dict(color='green'),
        name='Line 2',
        hovertemplate='dist: %{x}<br>temp: %{y}<extra></extra>'
    ))

    segments_dicts = []
    for i in range(len(segments_data["id"])):
        segments_dicts.append(dict(
            type="rect",
            xref="x",
            yref="paper",
            x0=segments_data["start"][i],
            x1=segments_data["end"][i],
            y0=0,
            y1=1,
            fillcolor=segments_data["colors_by_group"][i],
            opacity=0.3,
            layer="below",
            line_width=0,
        ))

    fig.update_layout(
        shapes=segments_dicts,
        width=1200,
        height=800,
        xaxis=dict(range=[0, 600], constrain='domain'),
        yaxis=dict(range=[-10, 60], constrain='domain'),
        hovermode='closest'
    )

    st.plotly_chart(fig, width="content")


if __name__ == "__main__":
    main()

