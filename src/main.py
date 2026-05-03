"""気象庁週間予報取得ツールのエントリポイント。"""

import logging
import os
import sys

from google.cloud import bigquery

from bigquery_client import write_forecasts
from config import get_locations, setup_logging
from fetcher import process_all_areas
from saver import save_data

logger = logging.getLogger(__name__)


def main() -> None:
    """ロギングを初期化し、予報データを取得・保存・BigQuery 書き込みする。

    全エリアの取得に失敗した場合は exit code 1 で終了する。
    GCP_PROJECT_ID が未設定の場合は BigQuery 書き込みをスキップする。
    """
    setup_logging()
    locations = get_locations()
    try:
        forecasts = process_all_areas(locations)
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)
    save_data(forecasts)

    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        logger.info("GCP_PROJECT_ID not set, skipping BigQuery write")
        return

    dataset_id = os.getenv("BQ_DATASET_ID", "weather_data")
    table_id = os.getenv("BQ_TABLE_ID", "jma_weekly_forecast")
    client = bigquery.Client(project=project_id)
    write_forecasts(client, forecasts, f"{project_id}.{dataset_id}.{table_id}")


if __name__ == "__main__":
    main()
