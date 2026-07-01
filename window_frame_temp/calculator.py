"""Steady-state vinyl window frame temperature calculator."""

from dataclasses import dataclass

from . import wind
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


def compute_frame_temperature(
    frame: FrameProfile,
    storey: int = 1,
    climate: ClimateDesignPoint = VANCOUVER_WINTER_DESIGN,
    indoor_film_coefficient_w_m2k: float = wind.INDOOR_FILM_COEFFICIENT_W_M2K,
) -> FrameTemperatureResult:
    """Solve the indoor-air -> frame -> outdoor-air series resistance network.

    Returns the interior- and exterior-facing frame surface temperatures,
    plus a CSA A440/NAFS-style temperature index and a simple condensation
    risk check against the indoor dew point.
    """
    site_wind_mps = wind.wind_speed_at_storey(climate.wind_speed_mps, storey)
    ho_actual = wind.exterior_film_coefficient(site_wind_mps)

    r_si = 1.0 / indoor_film_coefficient_w_m2k
    r_so = 1.0 / ho_actual
    r_frame = frame.conductive_resistance_m2k_w
    r_total = r_si + r_frame + r_so

    u_actual = 1.0 / r_total
    heat_flux = u_actual * (climate.indoor_temp_c - climate.outdoor_temp_c)

    t_interior = climate.indoor_temp_c - heat_flux * r_si
    t_exterior = climate.outdoor_temp_c + heat_flux * r_so

    dp = dew_point_c(climate.indoor_temp_c, climate.indoor_rh_pct)
    condensation_risk = t_interior <= dp

    span = climate.indoor_temp_c - climate.outdoor_temp_c
    temperature_index = (
        100.0 * (t_interior - climate.outdoor_temp_c) / span if span != 0 else 100.0
    )

    return FrameTemperatureResult(
        interior_surface_temp_c=t_interior,
        exterior_surface_temp_c=t_exterior,
        heat_flux_w_m2=heat_flux,
        u_factor_actual_w_m2k=u_actual,
        indoor_dew_point_c=dp,
        condensation_risk=condensation_risk,
        temperature_index_pct=temperature_index,
    )
