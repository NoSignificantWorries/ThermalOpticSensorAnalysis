import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from datetime import datetime
from pathlib import Path

from db_interface import ClickhouseConnect


def get_date_from_fiilename(filename: str):
    full_datetime_str = '_'.join(filename.split('_')[2:4])
    datetime_with_time = datetime.strptime(full_datetime_str, '%Y-%m-%d_%H-%M-%S')
    return datetime_with_time


def main(json_file: str) -> None:
    with open(json_file, "r") as file:
        data = json.load(file)

    for filepath in data["files"]:
        file = Path(filepath)

        if not file.exists():
            print("FILE NOT FOUND:", file)
            continue

    with ClickhouseConnect(["../.env"]) as db_connect:
        # rows = db_connect.execute_query(
        #     "SELECT name, engine FROM system.tables WHERE database = %(db)s",
        #     {'db': db_connect.config['database']}
        # )
        rows = db_connect.execute_query("SELECT * FROM measurements")
        print(rows)


if __name__ == "__main__":
    main("locals/target_csv.json")

