from __future__ import annotations

import argparse
from pathlib import Path

from solar import compute_solar_year, validate_inputs, write_records_csv
from visualization import plot_annual_2d, plot_annual_polar, plot_harmonic_fit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personal Observatory — Solar Cycle Visualization")
    parser.add_argument("--latitude", type=float, default=-34.9, help="Latitude in [-90, 90].")
    parser.add_argument("--longitude", type=float, default=138.6, help="Longitude in [-180, 180].")
    parser.add_argument("--timezone", type=str, default="Australia/Adelaide", help="IANA timezone (e.g., Australia/Adelaide).")
    parser.add_argument("--year", type=int, default=2026, help="Target year (positive integer).")
    parser.add_argument("--output", type=str, default="outputs", help="Output directory.")
    parser.add_argument("--harmonic", action="store_true", help="Generate optional harmonic daylight fit plot.")
    return parser.parse_args()


def run_pipeline(
    latitude: float,
    longitude: float,
    timezone_name: str,
    year: int,
    output_dir: Path,
    harmonic: bool = False,
) -> dict[str, Path]:
    validate_inputs(latitude, longitude, timezone_name, year)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = compute_solar_year(latitude, longitude, timezone_name, year)

    csv_path = output_dir / f"solar_{year}.csv"
    chart_2d_path = output_dir / f"solar_2d_{year}.png"
    chart_polar_path = output_dir / f"solar_polar_{year}.png"

    write_records_csv(records, csv_path)
    plot_annual_2d(records, latitude, year, chart_2d_path)
    plot_annual_polar(records, year, chart_polar_path)

    artifacts: dict[str, Path] = {
        "csv": csv_path,
        "plot_2d": chart_2d_path,
        "plot_polar": chart_polar_path,
    }
    if harmonic:
        harmonic_path = output_dir / f"daylight_harmonic_{year}.png"
        plot_harmonic_fit(records, year, harmonic_path)
        artifacts["plot_harmonic"] = harmonic_path

    return artifacts


def main() -> int:
    args = parse_args()
    try:
        artifacts = run_pipeline(
            latitude=args.latitude,
            longitude=args.longitude,
            timezone_name=args.timezone,
            year=args.year,
            output_dir=Path(args.output),
            harmonic=args.harmonic,
        )
    except ValueError as error:
        raise SystemExit(f"Input error: {error}") from error

    print("Generated files:")
    for key, path in artifacts.items():
        print(f"- {key}: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
