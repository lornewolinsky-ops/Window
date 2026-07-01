"""Solar loading on the exterior frame surface, by building elevation orientation."""

ORIENTATIONS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

# Approximate clear-sky peak solar irradiance on a vertical surface (W/m^2) at
# ~49.25N latitude (Vancouver). These are illustrative design values, not
# measured TMY data -- pass --solar-irradiance directly if you have local
# pyranometer/TMY data for a specific hour.
#
# "winter_design": the conservative worst case used for condensation-risk
# design (nighttime/overcast, no solar gain at all -- this matches how CSA
# A440/NFRC condensation resistance is actually tested, in a chamber with no
# solar load).
# "winter_sunny": a clear winter day at solar noon. Because the sun sits low
# in the sky in winter, south-facing surfaces receive strong direct gain
# while north gets only diffuse sky radiation.
# "summer_peak": clear-sky peak around the summer solstice. The high summer
# sun angle reduces south-facing gain but strongly increases east (morning)
# and west (afternoon) gain -- the classic case for dark vinyl frame
# overheating/warping on west elevations.
SOLAR_IRRADIANCE_TABLE_W_M2 = {
    "winter_design": {o: 0.0 for o in ORIENTATIONS},
    "winter_sunny": {
        "N": 40, "NE": 60, "E": 300, "SE": 480,
        "S": 560, "SW": 480, "W": 300, "NW": 60,
    },
    "summer_peak": {
        "N": 120, "NE": 480, "E": 650, "SE": 520,
        "S": 430, "SW": 520, "W": 650, "NW": 480,
    },
}

# Solar absorptivity of common vinyl frame colours. Darker colours absorb
# far more solar energy, which is why most vinyl extruders restrict dark
# colours (roughly above 0.70 absorptivity here) to specially heat-stabilized
# compounds -- standard vinyl can soften/warp if the profile runs too hot.
FRAME_COLOR_SOLAR_ABSORPTIVITY = {
    "white": 0.30,
    "almond": 0.45,
    "grey": 0.55,
    "bronze": 0.65,
    "black": 0.85,
}

# Commonly cited industry guidance for sustained vinyl profile temperature
# before heat distortion/warping risk becomes significant.
FRAME_DISTORTION_RISK_TEMP_C = 76.0


def solar_irradiance_w_m2(scenario: str, orientation: str) -> float:
    if scenario not in SOLAR_IRRADIANCE_TABLE_W_M2:
        valid = ", ".join(sorted(SOLAR_IRRADIANCE_TABLE_W_M2))
        raise ValueError(f"Unknown scenario '{scenario}'. Valid options: {valid}")
    table = SOLAR_IRRADIANCE_TABLE_W_M2[scenario]
    orientation = orientation.upper()
    if orientation not in table:
        raise ValueError(f"Unknown orientation '{orientation}'. Valid options: {ORIENTATIONS}")
    return table[orientation]


def frame_color_absorptivity(color: str) -> float:
    try:
        return FRAME_COLOR_SOLAR_ABSORPTIVITY[color]
    except KeyError as exc:
        valid = ", ".join(sorted(FRAME_COLOR_SOLAR_ABSORPTIVITY))
        raise ValueError(f"Unknown frame colour '{color}'. Valid options: {valid}") from exc
