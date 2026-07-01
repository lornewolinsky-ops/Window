"""Vancouver climate design data and psychrometric helpers."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ClimateDesignPoint:
    indoor_temp_c: float
    indoor_rh_pct: float
    outdoor_temp_c: float
    wind_speed_mps: float


# NBC 2020 / ASHRAE-style winter design conditions for Vancouver Intl Airport (YVR).
# Outdoor: January 2.5% dry-bulb design temperature. Indoor: typical heated
# residential setpoint with the reduced winter RH recommended by CSA/ASHRAE
# for condensation control on window frames (higher RH raises the dew point
# and therefore raises condensation risk for a given frame temperature).
VANCOUVER_WINTER_DESIGN = ClimateDesignPoint(
    indoor_temp_c=21.0,
    indoor_rh_pct=30.0,
    outdoor_temp_c=-7.1,
    wind_speed_mps=3.6,
)


def dew_point_c(air_temp_c: float, rh_pct: float) -> float:
    """Dew point via the Magnus-Tetens approximation (valid roughly -45..60C)."""
    if not 0 < rh_pct <= 100:
        raise ValueError("rh_pct must be in (0, 100]")
    a, b = 17.62, 243.12
    gamma = (a * air_temp_c) / (b + air_temp_c) + math.log(rh_pct / 100.0)
    return (b * gamma) / (a - gamma)
