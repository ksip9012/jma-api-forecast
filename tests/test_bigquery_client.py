from unittest.mock import MagicMock

from bigquery_client import write_forecasts
from models import Forecast


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


def test_write_forecasts_calls_load_table_from_json() -> None:
    mock_client = MagicMock()
    mock_job = MagicMock()
    mock_client.load_table_from_json.return_value = mock_job

    forecasts = [_make_forecast()]
    write_forecasts(mock_client, forecasts, "project.dataset.table")

    mock_client.load_table_from_json.assert_called_once()
    args, kwargs = mock_client.load_table_from_json.call_args
    assert args[0] is forecasts
    assert args[1] == "project.dataset.table"
    assert kwargs["job_config"].write_disposition == "WRITE_TRUNCATE"
    mock_job.result.assert_called_once()


def test_write_forecasts_passes_all_rows() -> None:
    mock_client = MagicMock()
    mock_client.load_table_from_json.return_value = MagicMock()

    forecasts = [_make_forecast(date=f"2026-05-0{i}") for i in range(1, 8)]
    write_forecasts(mock_client, forecasts, "project.dataset.table")

    args, _ = mock_client.load_table_from_json.call_args
    assert len(args[0]) == 7
