from config import get_locations
from models import AreaSetting


def test_get_locations_returns_area_settings() -> None:
    locations = get_locations()

    assert len(locations) > 0
    assert all(isinstance(loc, AreaSetting) for loc in locations)


def test_get_locations_has_required_fields() -> None:
    locations = get_locations()

    for loc in locations:
        assert loc.area_code
        assert loc.office_code
        assert loc.area_name
        assert loc.prefecture
        assert loc.location


def test_get_locations_default_count() -> None:
    locations = get_locations()

    assert len(locations) == 10
