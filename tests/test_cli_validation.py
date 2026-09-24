import pytest

from solar import validate_inputs


def test_validate_inputs_accepts_valid_default() -> None:
    tz = validate_inputs(-34.9, 138.6, "Australia/Adelaide", 2026)
    assert tz.key == "Australia/Adelaide"


@pytest.mark.parametrize(
    "latitude,longitude,timezone_name,year",
    [
        (91.0, 0.0, "Australia/Adelaide", 2026),
        (-91.0, 0.0, "Australia/Adelaide", 2026),
        (0.0, 181.0, "Australia/Adelaide", 2026),
        (0.0, -181.0, "Australia/Adelaide", 2026),
        (0.0, 0.0, "Invalid/Timezone", 2026),
        (0.0, 0.0, "Australia/Adelaide", 0),
    ],
)
def test_validate_inputs_rejects_invalid_values(
    latitude: float, longitude: float, timezone_name: str, year: int
) -> None:
    with pytest.raises(ValueError):
        validate_inputs(latitude, longitude, timezone_name, year)

