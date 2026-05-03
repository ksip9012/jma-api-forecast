import logging
import sys

from config import get_locations, setup_logging
from fetcher import process_all_areas
from saver import save_data

logger = logging.getLogger(__name__)


def main() -> None:
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
