import logging
import time

import requests

logger = logging.getLogger(__name__)

AREA_SETTINGS = [
    {"area_code": "130000",  "office_code": "130000", "area_name": "首都圏", "prefecture": "東京", "location": "東京"},
    {"area_code": "2710000", "office_code": "270000", "area_name": "近畿",   "prefecture": "大阪", "location": "大阪"},
    {"area_code": "400000",  "office_code": "400000", "area_name": "九州",   "prefecture": "福岡", "location": "福岡"},
    {"area_code": "370000",  "office_code": "370000", "area_name": "四国",   "prefecture": "香川", "location": "高松"},
    {"area_code": "340000",  "office_code": "340000", "area_name": "中国",   "prefecture": "広島", "location": "広島"},
    {"area_code": "2310000", "office_code": "230000", "area_name": "東海",   "prefecture": "愛知", "location": "名古屋"},
    {"area_code": "0410001", "office_code": "040000", "area_name": "東北",   "prefecture": "宮城", "location": "仙台"},
    {"area_code": "0110000", "office_code": "016000", "area_name": "北海道", "prefecture": "石狩", "location": "札幌"},
    {"area_code": "0920100", "office_code": "090000", "area_name": "北関東", "prefecture": "栃木", "location": "宇都宮"},
    {"area_code": "1720100", "office_code": "170000", "area_name": "北陸",   "prefecture": "石川", "location": "金沢"},
]

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


def _get_weekly_forecast_json(office_code: str) -> dict:
    url = _JMA_FORECAST_URL.format(office_code=office_code)
    headers = {"User-Agent": _USER_AGENT}
    res = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
    res.raise_for_status()
    return res.json()[_WEEKLY_FORECAST_INDEX]


def process_all_areas() -> list[dict]:
    all_forecasts = []
    skipped: list[str] = []

    for setting in AREA_SETTINGS:
        location = setting["location"]
        logger.info("Fetching: %s (%s)", location, setting["area_code"])
        try:
            weekly_data = _get_weekly_forecast_json(setting["office_code"])

            ts_weather = weekly_data["timeSeries"][_WEATHER_SERIES_INDEX]
            dates = ts_weather["timeDefines"]
            prefix = setting["area_code"][:_AREA_CODE_PREFIX_LEN]

            area_weather = next((a for a in ts_weather["areas"] if prefix in a["area"]["code"]), ts_weather["areas"][0])
            weather_codes = area_weather.get("weatherCodes", [])
            pops = area_weather.get("pops", [])
            reliabilities = area_weather.get("reliabilities", [])

            ts_temp = weekly_data["timeSeries"][_TEMP_SERIES_INDEX]
            area1 = next((a for a in ts_temp["areas"] if prefix in a["area"]["code"]), ts_temp["areas"][0])
            temps_min = area1.get("tempsMin", [])
            temps_max = area1.get("tempsMax", [])

            for i in range(len(dates)):
                all_forecasts.append({
                    "date": dates[i].split("T")[0],
                    "area_group": setting["area_name"],
                    "prefecture": setting["prefecture"],
                    "location": location,
                    "weather_code": weather_codes[i] if i < len(weather_codes) else "",
                    "pop": pops[i] if i < len(pops) else "",
                    "temp_min": temps_min[i] if i < len(temps_min) else "",
                    "temp_max": temps_max[i] if i < len(temps_max) else "",
                    "reliability": reliabilities[i] if i < len(reliabilities) else "",
                })

            time.sleep(_REQUEST_INTERVAL_SEC)

        except requests.exceptions.RequestException as e:
            logger.error("Network error fetching %s: %s", location, e)
            skipped.append(location)
        except (KeyError, IndexError, ValueError) as e:
            logger.error("Parse error fetching %s: %s", location, e)
            skipped.append(location)

    if skipped:
        logger.warning("Skipped %d / %d areas: %s", len(skipped), len(AREA_SETTINGS), skipped)

    if not all_forecasts:
        raise RuntimeError("All areas failed. No forecast data was collected.")

    return all_forecasts
