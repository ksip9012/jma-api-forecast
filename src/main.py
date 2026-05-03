from config import setup_logging
from fetcher import process_all_areas
from saver import save_data


def main() -> None:
    setup_logging()
    forecasts = process_all_areas()
    save_data(forecasts)


if __name__ == "__main__":
    main()
