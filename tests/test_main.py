from unittest.mock import patch

import pytest

from main import main
from models import AreaSetting, Forecast


def _make_location(location: str) -> AreaSetting:
    return AreaSetting(
        office_code="130000",
        weather_area_code="130010",
        temp_area_code="44132",
        area_name="首都圏",
        prefecture="東京",
        location=location,
    )


def _make_forecast(location: str) -> Forecast:
    return Forecast(
        date="2026-05-04",
        area_group="首都圏",
        prefecture="東京",
        location=location,
        weather_code="100",
        pop="10",
        temp_min="15",
        temp_max="22",
        reliability="A",
    )


def test_main_writes_to_bigquery_when_all_locations_succeed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    with (
        patch(
            "main.get_locations",
            return_value=[_make_location("東京"), _make_location("大阪")],
        ),
        patch(
            "main.process_all_areas",
            return_value=[_make_forecast("東京"), _make_forecast("大阪")],
        ),
        patch("main.save_data"),
        patch("main.bigquery.Client"),
        patch("main.write_forecasts") as mock_write,
    ):
        main()

    mock_write.assert_called_once()


def test_main_exits_without_writing_when_a_location_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    with (
        patch(
            "main.get_locations",
            return_value=[_make_location("東京"), _make_location("大阪")],
        ),
        patch("main.process_all_areas", return_value=[_make_forecast("東京")]),
        patch("main.save_data"),
        patch("main.bigquery.Client"),
        patch("main.write_forecasts") as mock_write,
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 1
    mock_write.assert_not_called()
