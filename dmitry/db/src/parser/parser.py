import re
import json
import secrets
import sqlite3
from pathlib import Path
from typing import Optional, Any

import polars as pl


LOWER_TEMP = -10
UPPER_TEMP = 60


class DBWork:
    def __init__(self, path: str, init_script: Optional[str] = None) -> None:
        self.path = pth(path, False)
        self.conn = sqlite3.connect(str(self.path))
        self.cur = self.conn.cursor()

        if init_script is not None:
            with open(str(pth(init_script)), 'r') as sql_file:
                sql_script = sql_file.read()

            self.cur.executescript(sql_script)
            self.conn.commit()

    def close(self):
        if self.conn is not None:
            self.conn.close()
        self.conn = None
        self.cur = None


def generate_secure_hex_color():
    return f"#{secrets.randbelow(256):02x}{secrets.randbelow(256):02x}{secrets.randbelow(256):02x}"


def error_handler(error_matches: Optional[dict[str, str]] = None, default: Optional[Any] = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                err_type = type(err).__name__
                if error_matches and err_type in error_matches:
                    print(error_matches[err_type])
                else:
                    print(f"Unexpected error '{err_type}' in function '{func.__name__}': {err}")
                return default
        return wrapper
    return decorator


def pth(path: str, check: bool = True) -> Path:
    path_obj = Path(path).expanduser()

    if not path_obj.exists() and check:
        raise FileNotFoundError(f"Not found path {path_obj}")

    return path_obj


@error_handler()
def open_df(path: str, columns: list[str] = ["dist", "temp"]):
    path_obj = pth(path)

    df = pl.read_csv(str(path_obj), has_header=False, separator=";")
    df = df.rename({"column_1": columns[0], "column_2": columns[1]})

    df_clipped = df.filter(pl.col(columns[1]).is_between(LOWER_TEMP, UPPER_TEMP))

    return df_clipped


# @error_handler()
def parse_config(path: str) -> dict:
    path_obj = pth(path)

    with open(str(path_obj), "r") as file:
        config = json.load(file)

    segments = config["SegmentCalculation"][0]["segParams"]

    segments_data = {
        "id": [],
        "group": [],
        "start": [],
        "end": [],
    }
    colors_by_id = {"seg_id": [], "color": []}
    groupes = {"group": [], "start": [], "end": [], "color": []}
    for seg in segments:
        for key in seg.keys():
            if key == "id":
                if seg[key] not in colors_by_id["seg_id"]:
                    color = generate_secure_hex_color()
                    colors_by_id["seg_id"].append(seg[key])
                    colors_by_id["color"].append(color)
            if key == "group":
                if seg[key] not in groupes["group"]:
                    color = generate_secure_hex_color()
                    groupes["group"].append(seg[key])
                    groupes["color"].append(color)
            segments_data[key].append(seg[key])

    seg_df = pl.DataFrame(segments_data)
    seg_df.write_csv("~/Projects/Data/new_COD/segments_config.csv")

    colors_id_df = pl.DataFrame(colors_by_id)
    colors_id_df.write_csv("~/Projects/Data/new_COD/colors_by_id.csv")

    for group in groupes["group"]:
        seg_by_df = seg_df.filter(pl.col("group") == group)
        # seg_by_df = seg_df[seg_df["group"] == group]
        groupes["start"].append(seg_by_df["start"].min())
        groupes["end"].append(seg_by_df["end"].max())

    groupes_df = pl.DataFrame(groupes)
    groupes_df.write_csv("~/Projects/Data/new_COD/groupes.csv")

    return segments_data


# @error_handler()
def main() -> None:
    # json_path = "~/Projects/Data/COD/Config_COD.json"
    # config_table = parse_config(json_path)

    # sensors_db_path = "~/Projects/Data/COD/sensors.db"
    # init_file = "~/Projects/ThermalOpticSensorAnalysis/dmitry/db/init.sql"
    # db = DBWork(sensors_db_path, init_file)

    input_folder = pth("~/Projects/Data/COD/COD_data")
    output_folder = pth("~/Projects/Data/new_COD/DATA")

    segments_df = pl.read_csv(str(pth("~/Projects/Data/new_COD/segments_config.csv")))

    pattern = re.compile(r'^(therm|refl)_(.+)\.csv$')
    datetime_pattern = r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})"

    time_stamps = []
    all_dfs = []
    for folder in input_folder.iterdir():
        if len(all_dfs) >= 2000:
            break

        if not folder.is_dir():
            continue
        for file in folder.rglob("therm_*.csv"):
            match = pattern.match(file.name)
            if match:
                _, suffix = match.groups()
                therm_file = folder / pth(f"therm_{suffix}.csv", False)
                refl_file = folder / pth(f"refl_{suffix}.csv", False)

                if not therm_file.exists() or not refl_file.exists():
                    continue

                timestamp_match = re.search(datetime_pattern, suffix)
                if timestamp_match:
                    timestamp = timestamp_match.group(1).replace("_", " ").replace("-", ":", 2)
                else:
                    timestamp = None

                therm_df = open_df(str(therm_file))
                # refl_df = open_df(str(refl_file), ["dist", "refl"])

                # full_df = therm_df.join(refl_df, on="dist", how="inner")

                df_therm_cross = therm_df.with_columns(pl.lit(1).alias("key"))
                df_segments_cross = segments_df.with_columns(pl.lit(1).alias("key"))

                result = (
                    df_therm_cross.join(df_segments_cross, on="key")
                    .filter(pl.col("dist").is_between(pl.col("start"), pl.col("end")))
                    .select(["id", "dist", "temp", "group"])
                    .join(therm_df, on=["temp", "dist"], how="right")
                )

                if timestamp is not None:
                    time_stamps.append(timestamp)

                full_df = result.with_columns(pl.lit(timestamp).alias("timestamp"))

                all_dfs.append(full_df)


    complex_df = pl.concat(all_dfs)

    complex_df.write_csv("~/Projects/Data/new_COD/data.csv")

    with open(pth("~/Projects/Data/new_COD/timestamps.json"), "w") as file:
        json.dump(time_stamps, file, indent=4)


if __name__ == "__main__":
    main()

