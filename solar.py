from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from astral import LocationInfo
    from astral.sun import sun
    ASTRAL_AVAILABLE = True
except ModuleNotFoundError:
    LocationInfo = None
    sun = None
    ASTRAL_AVAILABLE = False


@dataclass(slots=True)
class SolarDayRecord:
    day: date
    sunrise_local: datetime | None
    sunset_local: datetime | None
    sunrise_hour: float
    sunset_hour: float
    daylight_hours: float
    status: str


def validate_inputs(latitude: float, longitude: float, timezone_name: str, year: int) -> ZoneInfo:
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Invalid latitude {latitude}. Expected range: [-90, 90].")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Invalid longitude {longitude}. Expected range: [-180, 180].")
    if year < 1:
        raise ValueError(f"Invalid year {year}. Expected a positive integer year.")

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Invalid timezone '{timezone_name}'. Expected a valid IANA timezone."
        ) from exc


def iter_dates(year: int) -> Iterable[date]:
    current = date(year, 1, 1)
    stop = date(year + 1, 1, 1)
    while current < stop:
        yield current
        current += timedelta(days=1)


def _to_decimal_hour(value: datetime) -> float:
    return value.hour + value.minute / 60.0 + value.second / 3600.0


def _infer_missing_status(error: ValueError) -> str:
    message = str(error).lower()
    if "never rises" in message:
        return "polar_night"
    if "never sets" in message:
        return "polar_day"
    return "sun_event_unavailable"


def _normalize_angle(value: float) -> float:
    return value % 360.0


def _calculate_event_utc(day: date, latitude: float, longitude: float, is_sunrise: bool, zenith: float = 90.833) -> tuple[datetime | None, str | None]:
    n = day.timetuple().tm_yday
    lng_hour = longitude / 15.0
    approx_time = n + ((6.0 - lng_hour) / 24.0) if is_sunrise else n + ((18.0 - lng_hour) / 24.0)

    mean_anomaly = (0.9856 * approx_time) - 3.289
    true_longitude = _normalize_angle(
        mean_anomaly
        + (1.916 * math.sin(math.radians(mean_anomaly)))
        + (0.020 * math.sin(math.radians(2.0 * mean_anomaly)))
        + 282.634
    )

    right_ascension = math.degrees(math.atan(0.91764 * math.tan(math.radians(true_longitude))))
    right_ascension = _normalize_angle(right_ascension)
    l_quadrant = math.floor(true_longitude / 90.0) * 90.0
    ra_quadrant = math.floor(right_ascension / 90.0) * 90.0
    right_ascension = (right_ascension + l_quadrant - ra_quadrant) / 15.0

    sin_declination = 0.39782 * math.sin(math.radians(true_longitude))
    cos_declination = math.cos(math.asin(sin_declination))
    cos_hour_angle = (
        math.cos(math.radians(zenith))
        - (sin_declination * math.sin(math.radians(latitude)))
    ) / (cos_declination * math.cos(math.radians(latitude)))

    if cos_hour_angle > 1:
        return None, "polar_night"
    if cos_hour_angle < -1:
        return None, "polar_day"

    if is_sunrise:
        hour_angle = 360.0 - math.degrees(math.acos(cos_hour_angle))
    else:
        hour_angle = math.degrees(math.acos(cos_hour_angle))
    hour_angle /= 15.0

    local_mean_time = hour_angle + right_ascension - (0.06571 * approx_time) - 6.622
    utc_hour = (local_mean_time - lng_hour) % 24.0

    hours = int(utc_hour)
    minutes = int((utc_hour - hours) * 60.0)
    seconds_float = ((utc_hour - hours) * 60.0 - minutes) * 60.0
    seconds = int(round(seconds_float))

    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        hours += 1

    dt = datetime(day.year, day.month, day.day, tzinfo=ZoneInfo("UTC")) + timedelta(
        hours=hours, minutes=minutes, seconds=seconds
    )
    return dt, None


def _fallback_sunrise_sunset(day: date, latitude: float, longitude: float, tz: ZoneInfo) -> tuple[datetime | None, datetime | None, str]:
    sunrise_utc, sunrise_status = _calculate_event_utc(day, latitude, longitude, is_sunrise=True)
    sunset_utc, sunset_status = _calculate_event_utc(day, latitude, longitude, is_sunrise=False)

    status = "normal"
    if sunrise_status == "polar_day" or sunset_status == "polar_day":
        status = "polar_day"
    elif sunrise_status == "polar_night" or sunset_status == "polar_night":
        status = "polar_night"

    if sunrise_utc is None or sunset_utc is None:
        return None, None, status
    return sunrise_utc.astimezone(tz), sunset_utc.astimezone(tz), status


def compute_solar_year(
    latitude: float,
    longitude: float,
    timezone_name: str,
    year: int,
) -> list[SolarDayRecord]:
    tz = validate_inputs(latitude, longitude, timezone_name, year)
    location = (
        LocationInfo(name="target", region="custom", timezone=timezone_name, latitude=latitude, longitude=longitude)
        if ASTRAL_AVAILABLE
        else None
    )

    records: list[SolarDayRecord] = []
    for day in iter_dates(year):
        if ASTRAL_AVAILABLE and location is not None:
            try:
                values = sun(location.observer, date=day, tzinfo=tz)
                sunrise = values["sunrise"]
                sunset = values["sunset"]
                status = "normal"
            except ValueError as error:
                sunrise = None
                sunset = None
                status = _infer_missing_status(error)
        else:
            sunrise, sunset, status = _fallback_sunrise_sunset(day, latitude, longitude, tz)

        if sunrise is None or sunset is None:
            sunrise_hour = math.nan
            sunset_hour = math.nan
            daylight_hours = math.nan
        else:
            sunrise_hour = _to_decimal_hour(sunrise)
            sunset_hour = _to_decimal_hour(sunset)
            daylight_hours = (sunset - sunrise).total_seconds() / 3600.0
            if sunset_hour < sunrise_hour:
                status = "invalid_order"

        records.append(
            SolarDayRecord(
                day=day,
                sunrise_local=sunrise,
                sunset_local=sunset,
                sunrise_hour=sunrise_hour,
                sunset_hour=sunset_hour,
                daylight_hours=daylight_hours,
                status=status,
            )
        )
    return records


def write_records_csv(records: list[SolarDayRecord], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "date",
                "sunrise_local",
                "sunset_local",
                "sunrise_hour",
                "sunset_hour",
                "daylight_hours",
                "status",
            ]
        )
        for record in records:
            sunrise_hour = "" if math.isnan(record.sunrise_hour) else f"{record.sunrise_hour:.6f}"
            sunset_hour = "" if math.isnan(record.sunset_hour) else f"{record.sunset_hour:.6f}"
            daylight = "" if math.isnan(record.daylight_hours) else f"{record.daylight_hours:.6f}"
            writer.writerow(
                [
                    record.day.isoformat(),
                    "" if record.sunrise_local is None else record.sunrise_local.isoformat(),
                    "" if record.sunset_local is None else record.sunset_local.isoformat(),
                    sunrise_hour,
                    sunset_hour,
                    daylight,
                    record.status,
                ]
            )
