from unittest.mock import patch

import pytest
import requests

from fetcher import process_all_areas
from models import AreaSetting


def _make_location(
    office_code: str = "130000",
    location: str = "東京",
    weather_area_code: str = "130010",
    temp_area_code: str = "44132",
) -> AreaSetting:
    return AreaSetting(
        office_code=office_code,
        weather_area_code=weather_area_code,
        temp_area_code=temp_area_code,
        area_name="首都圏",
        prefecture="東京",
        location=location,
    )


def _make_weekly_data(
    dates: list[str],
    weather_area_code: str = "130010",
    temp_area_code: str = "44132",
) -> dict:
    return {
        "timeSeries": [
            {
                "timeDefines": [f"{d}T00:00:00+09:00" for d in dates],
                "areas": [
                    {
                        "area": {"code": weather_area_code},
                        "weatherCodes": ["100"] * len(dates),
                        "pops": ["10"] * len(dates),
                        "reliabilities": ["A"] * len(dates),
                    }
                ],
            },
            {
                "timeDefines": [f"{d}T00:00:00+09:00" for d in dates],
                "areas": [
                    {
                        "area": {"code": temp_area_code},
                        "tempsMin": ["15"] * len(dates),
                        "tempsMax": ["22"] * len(dates),
                    }
                ],
            },
        ]
    }


def test_process_all_areas_returns_correct_records() -> None:
    dates = ["2026-05-04", "2026-05-05", "2026-05-06"]
    mock_data = _make_weekly_data(dates)

    with patch("fetcher._get_weekly_forecast_json", return_value=mock_data):
        result = process_all_areas([_make_location()])

    assert len(result) == 3
    assert result[0]["date"] == "2026-05-04"
    assert result[0]["location"] == "東京"
    assert result[0]["weather_code"] == "100"
    assert result[0]["pop"] == "10"
    assert result[0]["temp_min"] == "15"
    assert result[0]["temp_max"] == "22"
    assert result[0]["reliability"] == "A"


def test_process_all_areas_raises_when_all_fail() -> None:
    with (
        patch(
            "fetcher._get_weekly_forecast_json",
            side_effect=requests.exceptions.ConnectionError("error"),
        ),
        pytest.raises(RuntimeError, match="All areas failed"),
    ):
        process_all_areas([_make_location()])


def test_process_all_areas_raises_on_parse_error() -> None:
    with (
        patch("fetcher._get_weekly_forecast_json", return_value={"timeSeries": []}),
        pytest.raises(RuntimeError, match="All areas failed"),
    ):
        process_all_areas([_make_location()])


def test_process_all_areas_partial_skip() -> None:
    locations = [
        _make_location(office_code="130000", location="東京"),
        _make_location(office_code="270000", location="大阪"),
    ]
    dates = ["2026-05-04", "2026-05-05"]
    mock_data = _make_weekly_data(dates)

    def side_effect(office_code: str) -> dict:
        if office_code == "130000":
            return mock_data
        raise requests.exceptions.ConnectionError("network error")

    with patch("fetcher._get_weekly_forecast_json", side_effect=side_effect):
        result = process_all_areas(locations)

    assert len(result) == 2
    assert all(r["location"] == "東京" for r in result)


def test_process_all_areas_uses_matching_area_not_first() -> None:
    mock_data = _make_weekly_data(["2026-05-04"])
    weather_areas = mock_data["timeSeries"][0]["areas"]
    temp_areas = mock_data["timeSeries"][1]["areas"]
    weather_areas.insert(
        0,
        {
            "area": {"code": "130020"},
            "weatherCodes": ["300"],
            "pops": ["90"],
            "reliabilities": ["C"],
        },
    )
    temp_areas.insert(
        0, {"area": {"code": "44172"}, "tempsMin": ["1"], "tempsMax": ["2"]}
    )

    with patch("fetcher._get_weekly_forecast_json", return_value=mock_data):
        result = process_all_areas([_make_location()])

    assert result[0]["weather_code"] == "100"
    assert result[0]["temp_min"] == "15"


@pytest.mark.parametrize(
    "codes",
    [
        {"weather_area_code": "999999"},
        {"temp_area_code": "99999"},
    ],
)
def test_process_all_areas_skips_when_area_code_not_found(
    codes: dict[str, str],
) -> None:
    mock_data = _make_weekly_data(["2026-05-04"])

    with (
        patch("fetcher._get_weekly_forecast_json", return_value=mock_data),
        pytest.raises(RuntimeError, match="All areas failed"),
    ):
        process_all_areas([_make_location(**codes)])
