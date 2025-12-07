import json
from pathlib import Path


def main(data_dir: str) -> None:
    data_dir_pth = Path(data_dir).expanduser().resolve()

    all_files = {
        "total": 0,
        "files": []
    }

    for subdir in data_dir_pth.iterdir():
        for file in subdir.iterdir():
            if not file.name.startswith("therm"):
                continue
            all_files["files"].append(str(file))
            all_files["total"] += 1

    with open("locals/target_csv.json", "w") as csv_file:
        json.dump(all_files, csv_file, indent=2)


if __name__ == "__main__":
    main("~/Projects/Data/COD/COD_data")


