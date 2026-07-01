"""Wind exposure and convective surface film coefficients."""

STOREY_HEIGHT_M = 3.2  # typical wood-frame residential floor-to-floor height
REFERENCE_HEIGHT_M = 10.0  # standard meteorological reference height for wind data
SUBURBAN_TERRAIN_EXPONENT = 0.25  # ASCE/NBC power-law exponent for suburban/urban terrain

INDOOR_FILM_COEFFICIENT_W_M2K = 8.29  # ASHRAE/NFRC standard winter indoor natural-convection value


def wind_speed_at_storey(reference_wind_mps: float, storey: int) -> float:
    """Estimate wind speed at a given storey using the atmospheric boundary-layer power law.

    Wind speed increases with height above grade, so upper-floor windows see a
    lower exterior surface resistance (more heat loss, colder frame) than
    ground-floor windows for the same reference weather-station wind speed.
    """
    if storey < 1:
        raise ValueError("storey must be >= 1")
    height_m = (storey - 0.5) * STOREY_HEIGHT_M
    return reference_wind_mps * (height_m / REFERENCE_HEIGHT_M) ** SUBURBAN_TERRAIN_EXPONENT


def exterior_film_coefficient(wind_speed_mps: float) -> float:
    """Outdoor convective film coefficient from wind speed (W/m^2K).

    Uses the widely cited McAdams correlation: h = 5.7 + 3.8*V for V up to
    ~5 m/s, switching to h = 7.2*V^0.78 for higher wind speeds.
    """
    if wind_speed_mps < 0:
        raise ValueError("wind_speed_mps must be >= 0")
    if wind_speed_mps <= 5.0:
        return 5.7 + 3.8 * wind_speed_mps
    return 7.2 * wind_speed_mps**0.78
