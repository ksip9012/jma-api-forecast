"""BigQuery への予報データ書き込み処理。"""

import logging
from typing import Any, cast

from google.cloud import bigquery

from models import Forecast

logger = logging.getLogger(__name__)

_SCHEMA = [
    bigquery.SchemaField("date", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("area_group", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("prefecture", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("location", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("weather_code", "STRING"),
    bigquery.SchemaField("pop", "STRING"),
    bigquery.SchemaField("temp_min", "STRING"),
    bigquery.SchemaField("temp_max", "STRING"),
    bigquery.SchemaField("reliability", "STRING"),
]


def write_forecasts(
    client: bigquery.Client,
    forecasts: list[Forecast],
    table_full_id: str,
) -> None:
    """予報レコードリストを BigQuery テーブルに WRITE_TRUNCATE で書き込む。

    週間予報は毎日上書きするため WRITE_TRUNCATE を使用する。

    Args:
        client: BigQuery クライアント。
        forecasts: 書き込む予報レコードのリスト。
        table_full_id: 対象テーブルのフル ID（例: project.dataset.table）。

    Raises:
        google.cloud.exceptions.GoogleCloudError: BigQuery への書き込みが失敗した場合。
    """
    job_config = bigquery.LoadJobConfig(
        schema=_SCHEMA,
        write_disposition="WRITE_TRUNCATE",
    )
    logger.info("Writing %d rows to %s", len(forecasts), table_full_id)
    client.load_table_from_json(
        cast(list[dict[str, Any]], forecasts),
        table_full_id,
        job_config=job_config,
    ).result()
    logger.info("Wrote %d rows to %s", len(forecasts), table_full_id)
