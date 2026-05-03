"""気象庁 JSON API から週間予報データを取得・パースするモジュール。"""

import logging
import time
from typing import Any

import requests

from models import AreaSetting, Forecast

logger = logging.getLogger(__name__)

_JMA_FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_REQUEST_TIMEOUT = 10
_REQUEST_INTERVAL_SEC = 0.5
# 気象庁APIのレスポンスは [0]=今日明日予報, [1]=週間予報 の構造
_WEEKLY_FORECAST_INDEX = 1
# 週間予報内 timeSeries: [0]=天気・降水確率・信頼度, [1]=気温
_WEATHER_SERIES_INDEX = 0
_TEMP_SERIES_INDEX = 1
# エリアコードの前方5文字でtimeSeriesのareaとマッチングする
_AREA_CODE_PREFIX_LEN = 5


def _get_weekly_forecast_json(office_code: str) -> dict[str, Any]:
    """気象庁 API から指定オフィスの週間予報 JSON を取得する。

    Args:
        office_code: 気象庁の府県予報区コード。

    Returns:
        週間予報データの辞書（API レスポンスの index 1 に相当）。

    Raises:
        requests.exceptions.RequestException: ネットワークエラーまたは HTTP エラーが発生した場合。
    """
    url = _JMA_FORECAST_URL.format(office_code=office_code)
    headers = {"User-Agent": _USER_AGENT}
    res = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
    res.raise_for_status()
    return res.json()[_WEEKLY_FORECAST_INDEX]  # type: ignore[no-any-return]


def process_all_areas(locations: list[AreaSetting]) -> list[Forecast]:
    """指定された全エリアの週間予報を取得してフラットなレコードリストを返す。

    各エリアで API 取得またはパースに失敗した場合はスキップしてログに記録する。
    全エリアが失敗した場合は RuntimeError を送出する。

    Args:
        locations: 取得対象の予報エリアリスト。

    Returns:
        list[Forecast]: 全エリア・全日付のフラットな予報レコードリスト。

    Raises:
        RuntimeError: 全エリアで取得・パースに失敗し、データが1件も得られなかった場合。
    """
    all_forecasts: list[Forecast] = []
    skipped: list[str] = []

    for setting in locations:
        logger.info("Fetching: %s (%s)", setting.location, setting.area_code)
        try:
            weekly_data = _get_weekly_forecast_json(setting.office_code)

            ts_weather = weekly_data["timeSeries"][_WEATHER_SERIES_INDEX]
            dates: list[str] = ts_weather["timeDefines"]
            prefix = setting.area_code[:_AREA_CODE_PREFIX_LEN]

            area_weather = next((a for a in ts_weather["areas"] if prefix in a["area"]["code"]), ts_weather["areas"][0])
            weather_codes: list[str] = area_weather.get("weatherCodes", [])
            pops: list[str] = area_weather.get("pops", [])
            reliabilities: list[str] = area_weather.get("reliabilities", [])

            ts_temp = weekly_data["timeSeries"][_TEMP_SERIES_INDEX]
            area_temp = next((a for a in ts_temp["areas"] if prefix in a["area"]["code"]), ts_temp["areas"][0])
            temps_min: list[str] = area_temp.get("tempsMin", [])
            temps_max: list[str] = area_temp.get("tempsMax", [])

            for i in range(len(dates)):
                all_forecasts.append(Forecast(
                    date=dates[i].split("T")[0],
                    area_group=setting.area_name,
                    prefecture=setting.prefecture,
                    location=setting.location,
                    weather_code=weather_codes[i] if i < len(weather_codes) else "",
                    pop=pops[i] if i < len(pops) else "",
                    temp_min=temps_min[i] if i < len(temps_min) else "",
                    temp_max=temps_max[i] if i < len(temps_max) else "",
                    reliability=reliabilities[i] if i < len(reliabilities) else "",
                ))

            time.sleep(_REQUEST_INTERVAL_SEC)

        except requests.exceptions.RequestException as e:
            logger.error("Network error fetching %s: %s", setting.location, e)
            skipped.append(setting.location)
        except (KeyError, IndexError, ValueError) as e:
            logger.error("Parse error fetching %s: %s", setting.location, e)
            skipped.append(setting.location)

    if skipped:
        logger.warning("Skipped %d / %d areas: %s", len(skipped), len(locations), skipped)

    if not all_forecasts:
        raise RuntimeError("All areas failed. No forecast data was collected.")

    return all_forecasts
