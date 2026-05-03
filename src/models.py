from typing import TypedDict

from pydantic import BaseModel


class AreaSetting(BaseModel):
    """気象庁の予報エリア設定を定義するモデル。"""

    area_code: str
    office_code: str
    area_name: str
    prefecture: str
    location: str


class Forecast(TypedDict):
    """1地点・1日分の週間予報データ。"""

    date: str
    area_group: str
    prefecture: str
    location: str
    weather_code: str
    pop: str
    temp_min: str
    temp_max: str
    reliability: str
