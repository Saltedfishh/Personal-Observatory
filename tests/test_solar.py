from datetime import date
import pytest

from solar import compute_solar_year, iter_dates


def test_day_count_regular_and_leap_year() -> None:
    regular = list(iter_dates(2025))
    leap = list(iter_dates(2024))
    assert len(regular) == 365
    assert len(leap) == 366


def _get_record(records, target_day: date):
    matched = [record for record in records if record.day == target_day]
    assert len(matched) == 1
    return matched[0]


def test_sunrise_before_sunset_on_normal_day() -> None:
    records = compute_solar_year(-34.9, 138.6, "Australia/Adelaide", 2026)
    rec = _get_record(records, date(2026, 6, 15))
    assert rec.status == "normal"
    assert rec.sunrise_hour < rec.sunset_hour


def test_southern_hemisphere_summer_longer_than_winter() -> None:
    records = compute_solar_year(-34.9, 138.6, "Australia/Adelaide", 2026)
    summer = _get_record(records, date(2026, 12, 21))
    winter = _get_record(records, date(2026, 6, 21))
    assert summer.daylight_hours > winter.daylight_hours


def test_dst_offsets_switch_in_adelaide() -> None:
    records = compute_solar_year(-34.9, 138.6, "Australia/Adelaide", 2026)
    ordered_offsets = [
        record.sunrise_local.strftime("%z")
        for record in records
        if record.sunrise_local is not None
    ]
    assert "+0930" in ordered_offsets
    assert "+1030" in ordered_offsets

    pairs = list(zip(ordered_offsets[:-1], ordered_offsets[1:]))
    assert ("+1030", "+0930") in pairs
    assert ("+0930", "+1030") in pairs


def test_hangzhou_summer_longer_than_winter() -> None:
    records = compute_solar_year(30.2741, 120.1551, "Asia/Shanghai", 2026)
    summer = _get_record(records, date(2026, 6, 21))
    winter = _get_record(records, date(2026, 12, 21))

    assert summer.status == "normal"
    assert winter.status == "normal"
    assert summer.daylight_hours > winter.daylight_hours
