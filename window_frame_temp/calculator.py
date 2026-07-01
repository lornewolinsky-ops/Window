"""Steady-state vinyl window frame temperature calculator."""

from dataclasses import dataclass
from typing import Optional

from . import solar, wind
from .climate import ClimateDesignPoint, VANCOUVER_WINTER_DESIGN, dew_point_c
from .frame import FrameProfile, get_frame_profile


@dataclass(frozen=True)
class FrameTemperatureResult:
    interior_surface_temp_c: float
    exterior_surface_temp_c: float
    heat_flux_w_m2: float
    u_factor_actual_w_m2k: float
    indoor_dew_point_c: float
    condensation_risk: bool
    temperature_index_pct: float
    sol_air_temp_c: float
    solar_irradiance_w_m2: float
    frame_distortion_risk: bool


def compute_frame_temperature(
    frame: FrameProfile,
    storey: int = 1,
    climate: ClimateDesignPoint = VANCOUVER_WINTER_DESIGN,
    indoor_film_coefficient_w_m2k: float = wind.INDOOR_FILM_COEFFICIENT_W_M2K,
    orientation: str = "S",
    frame_color: str = "white",
    solar_scenario: str = "winter_design",
    solar_irradiance_override_w_m2: Optional[float] = None,
) -> FrameTemperatureResult:
    """Solve the indoor-air -> frame -> outdoor-air series resistance network.

    Solar gain absorbed by the exterior frame surface is folded in via the
    sol-air temperature method (ASHRAE): the outdoor air temperature seen by
    the exterior film resistance is raised by (absorbed solar flux / exterior
    film coefficient), which lets the same series-resistance algebra be
    reused unchanged. `orientation` and `solar_scenario` pick a table look-up
    for incident irradiance (see solar.py); pass `solar_irradiance_override_w_m2`
    to use a measured/TMY value instead.

    The CSA A440-style temperature index is still computed against the true
    ambient outdoor air temperature (not sol-air), matching how that index is
    actually measured -- in a chamber, with no solar load.

    Returns the interior- and exterior-facing frame surface temperatures, a
    condensation risk check against the indoor dew point, and a frame heat
    distortion risk flag for solar-warmed dark frames.
    """
    site_wind_mps = wind.wind_speed_at_storey(climate.wind_speed_mps, storey)
    ho_actual = wind.exterior_film_coefficient(site_wind_mps)

    r_si = 1.0 / indoor_film_coefficient_w_m2k
    r_so = 1.0 / ho_actual
    r_frame = frame.conductive_resistance_m2k_w
    r_total = r_si + r_frame + r_so

    if solar_irradiance_override_w_m2 is not None:
        irradiance = solar_irradiance_override_w_m2
    else:
        irradiance = solar.solar_irradiance_w_m2(solar_scenario, orientation)
    absorptivity = solar.frame_color_absorptivity(frame_color)
    absorbed_solar_flux = absorptivity * irradiance
    sol_air_temp = climate.outdoor_temp_c + absorbed_solar_flux * r_so

    u_actual = 1.0 / r_total
    heat_flux = u_actual * (climate.indoor_temp_c - sol_air_temp)

    t_interior = climate.indoor_temp_c - heat_flux * r_si
    t_exterior = sol_air_temp + heat_flux * r_so

    dp = dew_point_c(climate.indoor_temp_c, climate.indoor_rh_pct)
    condensation_risk = t_interior <= dp

    span = climate.indoor_temp_c - climate.outdoor_temp_c
    temperature_index = (
        100.0 * (t_interior - climate.outdoor_temp_c) / span if span != 0 else 100.0
    )

    frame_distortion_risk = t_exterior >= solar.FRAME_DISTORTION_RISK_TEMP_C

    return FrameTemperatureResult(
        interior_surface_temp_c=t_interior,
        exterior_surface_temp_c=t_exterior,
        heat_flux_w_m2=heat_flux,
        u_factor_actual_w_m2k=u_actual,
        indoor_dew_point_c=dp,
        condensation_risk=condensation_risk,
        temperature_index_pct=temperature_index,
        sol_air_temp_c=sol_air_temp,
        solar_irradiance_w_m2=irradiance,
        frame_distortion_risk=frame_distortion_risk,
    )
