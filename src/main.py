"""気象庁週間予報取得ツールのエントリポイント。"""

import logging
import sys

from config import get_locations, setup_logging
from fetcher import process_all_areas
from saver import save_data

logger = logging.getLogger(__name__)


def main() -> None:
    """ロギングを初期化し、予報データを取得して保存する。

    全エリアの取得に失敗した場合は exit code 1 で終了する。
    """
    setup_logging()
    locations = get_locations()
    try:
        forecasts = process_all_areas(locations)
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)
    save_data(forecasts)


if __name__ == "__main__":
    main()
