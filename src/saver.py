"""予報データを CSV および JSON ファイルに保存するモジュール。"""

import csv
import json
import logging
from pathlib import Path

from models import Forecast

logger = logging.getLogger(__name__)

_DATA_DIR = Path("data")
_CSV_FIELDNAMES = ["date", "area_group", "prefecture", "location", "weather_code", "pop", "temp_min", "temp_max", "reliability"]


def save_data(forecasts: list[Forecast]) -> None:
    """予報レコードリストを data/ ディレクトリに CSV および JSON で保存する。

    forecasts が空の場合は JSON のみ保存し、CSV は生成しない。

    Args:
        forecasts: 保存対象の予報レコードリスト。

    Side effects:
        - data/all_forecasts.json を上書き保存する。
        - forecasts が空でない場合、data/all_forecasts.csv を上書き保存する。
    """
    _DATA_DIR.mkdir(exist_ok=True)

    json_path = _DATA_DIR / "all_forecasts.json"
    json_path.write_text(
        json.dumps(forecasts, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )

    csv_path = _DATA_DIR / "all_forecasts.csv"
    if forecasts:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(forecasts)
        logger.info("Saved %d rows to %s and %s", len(forecasts), json_path, csv_path)
    else:
        logger.warning("No forecasts to save. JSON saved to %s", json_path)
