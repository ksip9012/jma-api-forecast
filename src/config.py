"""ロギング設定と地点設定の読み込みロジック。"""

import logging
import tomllib
from pathlib import Path

from models import AreaSetting

_LOCATIONS_TOML = Path(__file__).parent / "locations.toml"


def setup_logging() -> None:
    """ロギングの初期設定を行う。

    エントリポイント（main.py）から1回だけ呼び出す。
    各モジュールは logging.getLogger(__name__) のみ使用し、
    この関数は呼び出さない。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def get_locations() -> list[AreaSetting]:
    """locations.toml から予報エリアのリストを読み込んで返す。

    Returns:
        list[AreaSetting]: locations.toml に定義された予報エリアのリスト。

    Raises:
        FileNotFoundError: locations.toml が存在しない場合。
        KeyError: locations.toml に "locations" キーが存在しない場合。
        ValidationError: エントリが AreaSetting のスキーマに適合しない場合。
    """
    with _LOCATIONS_TOML.open("rb") as f:
        data = tomllib.load(f)
    return [AreaSetting.model_validate(item) for item in data["locations"]]
