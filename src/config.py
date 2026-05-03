import logging
import tomllib
from pathlib import Path

from models import AreaSetting

_LOCATIONS_TOML = Path(__file__).parent / "locations.toml"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def get_locations() -> list[AreaSetting]:
    with _LOCATIONS_TOML.open("rb") as f:
        data = tomllib.load(f)
    return [AreaSetting.model_validate(item) for item in data["locations"]]
