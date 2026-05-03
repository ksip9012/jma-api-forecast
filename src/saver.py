import csv
import json
import logging
import os

from models import Forecast

logger = logging.getLogger(__name__)

_CSV_FIELDNAMES = ["date", "area_group", "prefecture", "location", "weather_code", "pop", "temp_min", "temp_max", "reliability"]


def save_data(forecasts: list[Forecast]) -> None:
    os.makedirs("data", exist_ok=True)

    json_path = os.path.join("data", "all_forecasts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(forecasts, f, ensure_ascii=False, indent=4)

    csv_path = os.path.join("data", "all_forecasts.csv")
    if forecasts:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(forecasts)
        logger.info("Saved %d rows to %s and %s", len(forecasts), json_path, csv_path)
    else:
        logger.warning("No forecasts to save. JSON saved to %s", json_path)
