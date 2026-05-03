import json
from pathlib import Path

import pytest

from models import Forecast
from saver import save_data


def _make_forecast(date: str = "2026-05-04", location: str = "東京") -> Forecast:
    return Forecast(
        date=date,
        area_group="首都圏",
        prefecture="東京",
        location=location,
        weather_code="100",
        pop="10",
        temp_min="15",
        temp_max="22",
        reliability="A",
    )


def test_save_data_creates_json_and_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    save_data([_make_forecast("2026-05-04"), _make_forecast("2026-05-05")])

    assert (tmp_path / "data" / "all_forecasts.json").exists()
    assert (tmp_path / "data" / "all_forecasts.csv").exists()


def test_save_data_json_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    save_data([_make_forecast("2026-05-04")])

    data = json.loads((tmp_path / "data" / "all_forecasts.json").read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["date"] == "2026-05-04"
    assert data[0]["location"] == "東京"


def test_save_data_empty_forecasts_no_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    save_data([])  # Issue #1 のバグ修正確認: NameError が出ないこと

    assert (tmp_path / "data" / "all_forecasts.json").exists()
    assert not (tmp_path / "data" / "all_forecasts.csv").exists()
