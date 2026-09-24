from __future__ import annotations

from datetime import date
from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np

from solar import SolarDayRecord


def _hour_to_theta(hour: float) -> float:
    return 2.0 * np.pi * (hour / 24.0)


def _daylight_intervals(sunrise: float, sunset: float) -> list[tuple[float, float]]:
    if sunset >= sunrise:
        return [(sunrise, sunset)]
    return [(sunrise, 24.0), (0.0, sunset)]


def plot_annual_2d(records: list[SolarDayRecord], latitude: float, year: int, output_file: Path) -> None:
    dates = np.array([record.day for record in records], dtype=object)
    sunrise = np.array([record.sunrise_hour for record in records], dtype=float)
    sunset = np.array([record.sunset_hour for record in records], dtype=float)
    valid = np.isfinite(sunrise) & np.isfinite(sunset)

    fig, ax = plt.subplots(figsize=(13, 6), layout="constrained")
    ax.plot(dates, sunrise, label="Sunrise", color="#3366cc", linewidth=1.5)
    ax.plot(dates, sunset, label="Sunset", color="#cc3300", linewidth=1.5)
    ax.fill_between(dates, sunrise, sunset, where=valid, color="#ffcc66", alpha=0.35, label="Daylight")

    ax.set_ylim(0, 24)
    ax.set_yticks(np.arange(0, 25, 2))
    ax.set_ylabel("Local clock time (hours)")
    ax.set_xlabel("Date")
    ax.set_title(f"Annual Sunrise/Sunset ({year})")
    ax.grid(alpha=0.25)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    markers: dict[str, date] = {
        "Mar Equinox (~3/20)": date(year, 3, 20),
        "Jun Solstice (~6/21)": date(year, 6, 21),
        "Sep Equinox (~9/22)": date(year, 9, 22),
        "Dec Solstice (~12/21)": date(year, 12, 21),
    }
    for label, marker_date in markers.items():
        ax.axvline(marker_date, linestyle="--", linewidth=0.8, color="gray", alpha=0.6)
        ax.text(marker_date, 23.5, label, rotation=90, va="top", ha="center", fontsize=8)

    note = "Southern hemisphere seasons are opposite to northern hemisphere." if latitude < 0 else "Northern hemisphere seasonal convention."
    ax.text(0.01, 0.01, note, transform=ax.transAxes, fontsize=9, alpha=0.8)
    ax.legend(loc="lower right")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=160)
    plt.close(fig)


def plot_annual_polar(records: list[SolarDayRecord], year: int, output_file: Path) -> None:
    fig = plt.figure(figsize=(10, 10), layout="constrained")
    ax = fig.add_subplot(111, projection="polar")

    total_days = len(records)
    for index, record in enumerate(records, start=1):
        if not (math.isfinite(record.sunrise_hour) and math.isfinite(record.sunset_hour)):
            continue
        for start_hour, end_hour in _daylight_intervals(record.sunrise_hour, record.sunset_hour):
            theta_start = _hour_to_theta(start_hour)
            theta_end = _hour_to_theta(end_hour)
            theta_center = (theta_start + theta_end) / 2.0
            width = max(theta_end - theta_start, 1e-6)
            ax.bar(
                theta_center,
                0.85,
                width=width,
                bottom=index - 0.45,
                color="#ffb347",
                alpha=0.58,
                edgecolor="none",
                align="center",
            )

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetagrids([0, 90, 180, 270], labels=["00:00", "06:00", "12:00", "18:00"])
    ax.set_title(f"Solar Cycle Polar View ({year})", va="bottom")

    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_days = [date(year, month, 1).timetuple().tm_yday for month in range(1, 13)]
    ax.set_rgrids(month_days, labels=month_labels, angle=67.5)
    ax.set_rmax(total_days + 1)
    ax.grid(alpha=0.35)
    ax.legend(handles=[Patch(facecolor="#ffb347", alpha=0.58, label="Daylight arc")], loc="upper right", bbox_to_anchor=(1.18, 1.08))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=160)
    plt.close(fig)


def plot_harmonic_fit(records: list[SolarDayRecord], year: int, output_file: Path) -> float:
    total_days = len(records)
    day_index = np.arange(1, total_days + 1, dtype=float)
    observed = np.array([record.daylight_hours for record in records], dtype=float)
    valid = np.isfinite(observed)

    angle = 2.0 * np.pi * day_index / total_days
    design_matrix = np.column_stack([np.ones(total_days), np.sin(angle), np.cos(angle)])
    coeffs, *_ = np.linalg.lstsq(design_matrix[valid], observed[valid], rcond=None)
    fitted = design_matrix @ coeffs

    rmse = float(np.sqrt(np.mean((observed[valid] - fitted[valid]) ** 2)))

    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    ax.plot(day_index, observed, color="#333333", linewidth=1.2, label="Observed daylight")
    ax.plot(day_index, fitted, color="#d62728", linewidth=2.0, label="First-order harmonic fit")
    ax.set_xlabel("Day of year")
    ax.set_ylabel("Daylight hours")
    ax.set_title(f"Daylight Harmonic Approximation ({year}) | RMSE={rmse:.3f} h")
    ax.grid(alpha=0.3)
    ax.legend(loc="best")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=160)
    plt.close(fig)

    return rmse

