from pathlib import Path

from main import run_pipeline


def test_pipeline_outputs_are_generated(tmp_path: Path) -> None:
    artifacts = run_pipeline(
        latitude=-34.9,
        longitude=138.6,
        timezone_name="Australia/Adelaide",
        year=2026,
        output_dir=tmp_path,
        harmonic=True,
    )

    expected = {"csv", "plot_2d", "plot_polar", "plot_harmonic"}
    assert expected.issubset(artifacts.keys())

    for path in artifacts.values():
        assert path.exists()
        assert path.stat().st_size > 0

