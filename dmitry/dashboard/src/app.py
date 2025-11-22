import json
import secrets
from pathlib import Path
from typing import Optional, Any

import polars as pl
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


@error_handler()
def open_config(path: str) -> dict:
    path_obj = pth(path)

    with open(str(path_obj), "r") as file:
        return json.load(file)


@error_handler()
def open_df(path: str):
    path_obj = pth(path)

    df = pl.read_csv(str(path_obj), has_header=False, separator=";")
    df = df.rename({"column_1": "dist", "column_2": "temp"})

    df_clipped = df.filter(pl.col("temp").is_between(-10, 120))

    return df_clipped


def main():
    json_path = "~/Projects/Data/COD/Config_COD.json"
    config = open_config(json_path)
    segments = config["SegmentCalculation"][0]["segParams"]

    segments_data = {
        "id": [],
        "group": [],
        "start": [],
        "end": [],
        "colors_by_id": [],
        "colors_by_group": [],
    }
    colors_by_id = {}
    colors_by_group = {}
    for seg in segments:
        for key in seg.keys():
            if key == "id":
                if seg[key] not in colors_by_id.keys():
                    color = generate_secure_hex_color()
                    colors_by_id[seg[key]] = color
                else:
                    color = colors_by_id[seg[key]]
                segments_data["colors_by_id"].append(color)
            if key == "group":
                if seg[key] not in colors_by_group.keys():
                    color = generate_secure_hex_color()
                    colors_by_group[seg[key]] = color
                else:
                    color = colors_by_group[seg[key]]
                segments_data["colors_by_group"].append(color)
            segments_data[key].append(seg[key])

    seg_df = pl.DataFrame(segments_data)

    base_data_obj = pth("~/Projects/Data/COD/COD_data")

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

    # line1 = alt.Chart(df1).mark_line(color="red").encode(
    #     x=alt.X("dist:Q", scale=alt.Scale(
    #         domain=[0, 600],
    #         clamp=True
    #     )),
    #     y=alt.Y("temp:Q", scale=alt.Scale(
    #         domain=[-10, 120],
    #         clamp=True
    #     )),
    #     tooltip=["dist:Q", "temp:Q"])
    #
    # line2 = alt.Chart(df2).mark_line(color="green").encode(
    #     x=alt.X("dist:Q", scale=alt.Scale(
    #         domain=[0, 600],
    #         clamp=True
    #     )),
    #     y=alt.Y("temp:Q", scale=alt.Scale(
    #         domain=[-10, 120],
    #         clamp=True
    #     )),
    #     tooltip=["dist:Q", "temp:Q"])
    #
    # layer_chart = alt.layer(line1, line2, seg_chart).interactive(bind_x=False).resolve_scale(y="shared").properties(width=1200, height=800)
    #
    # st.altair_chart(layer_chart, width="content")


if __name__ == "__main__":
    main()

