# Vinyl Window Frame Temperature Calculator

Estimates the steady-state surface temperature of a vinyl window frame in a
wood-frame residential building, for the specific case of a six-storey
building in Vancouver, BC. It is meant as a quick building-science hand
calculation (the kind used to sanity-check condensation risk), not a
replacement for full 2D/3D finite-element frame simulation (e.g. THERM /
NFRC-certified simulation).

## Method

The window frame is modeled as a 1D series thermal resistance network:

```
indoor air --[R_si]-- frame interior surface --[R_frame]-- frame exterior surface --[R_so]-- outdoor air
```

- **R_si**: indoor natural-convection film resistance (fixed ASHRAE/NFRC
  winter value, 8.29 W/m²K).
- **R_frame**: the vinyl frame's own conductive resistance. This is backed
  out of a whole-frame NFRC/CSA-A440 U-factor (which is simulated/tested with
  standard boundary films already included) by subtracting the standard NFRC
  film resistances, so it can be recombined with the *actual* site film
  coefficients used here.
- **R_so**: outdoor convective film resistance, computed from wind speed via
  the McAdams correlation. Wind speed is adjusted for storey height using an
  atmospheric boundary-layer power law, since upper floors of a six-storey
  building see higher wind speeds (and therefore colder frame temperatures)
  than the ground floor for the same weather-station wind reading.

Given indoor/outdoor design temperatures, the heat flux through the frame is
`q = U_actual * (T_indoor - T_outdoor)`, and the two surface temperatures
follow directly from `q` and the film resistances on each side.

The calculator also reports:
- **Indoor dew point** (Magnus-Tetens formula) and a **condensation risk**
  flag (interior frame surface temp <= dew point).
- A **CSA A440 / NAFS-style temperature index**: `100 * (T_interior -
  T_outdoor) / (T_indoor - T_outdoor)`, the standard metric used in Canadian
  fenestration condensation-resistance ratings. This is always computed
  against the true ambient outdoor air temperature (not sol-air), matching
  how the index is actually measured -- in a chamber, with no solar load. It
  can go outside the usual 0-100% range under strong solar gain, since that's
  outside what the index was designed to describe.
- A **frame heat distortion risk** flag for solar-warmed dark frames (see
  below).

## Orientation and frame colour (solar gain)

Solar radiation absorbed by the exterior frame surface is folded into the
same resistance network using the standard **sol-air temperature** method
(ASHRAE): the effective outdoor temperature seen by the exterior film
resistance is raised by `(absorptivity * incident irradiance) / h_o`. This
means a sunlit dark frame can end up much hotter than the ambient air, and
the heat flow can even reverse (flow inward) under strong solar load.

`--orientation` (`N/NE/E/SE/S/SW/W/NW`) and `--solar-scenario` select a
peak clear-sky irradiance from an approximate table for ~49.25°N latitude
(Vancouver):

| Scenario | Meaning |
|---|---|
| `winter_design` (default) | No solar at all -- nighttime/overcast worst case used for condensation-risk design, matching how CSA A440/NFRC condensation resistance is actually tested (no solar load). |
| `winter_sunny` | Clear winter day at solar noon. Low sun angle means south gets strong direct gain, north gets only diffuse. |
| `summer_peak` | Clear-sky peak near the summer solstice. High sun angle reduces south gain but boosts east (morning) and west (afternoon) -- the classic case for dark vinyl frame overheating on west elevations. |

These are illustrative design values, not measured Vancouver TMY data --
pass `--solar-irradiance <W/m^2>` directly if you have local solar data for
a specific hour.

`--frame-colour` sets the frame's solar absorptivity:

| Colour | Absorptivity |
|---|---|
| `white` (default) | 0.30 |
| `almond` | 0.45 |
| `grey` | 0.55 |
| `bronze` | 0.65 |
| `black` | 0.85 |

Darker colours absorb far more solar energy -- this is why vinyl extruders
generally restrict dark colours to specially heat-stabilized compounds. The
calculator flags `frame_distortion_risk` when the exterior surface exceeds
76 °C, a commonly cited threshold for vinyl profile heat distortion/warping.

## Default climate: Vancouver winter design conditions

| Parameter | Default | Note |
|---|---|---|
| Indoor temperature | 21.0 °C | typical heated residential setpoint |
| Indoor RH | 30% | reduced winter RH recommended for condensation control |
| Outdoor temperature | -7.1 °C | NBC/ASHRAE-style Jan 2.5% design temperature, YVR |
| Reference wind speed | 3.6 m/s | 10 m reference height |

All of these can be overridden on the command line.

## Frame presets

| Preset | NFRC whole-frame U-factor (W/m²K) |
|---|---|
| `standard_vinyl` | 2.5 |
| `multi_chamber_vinyl` | 2.0 |
| `foam_filled_vinyl` | 1.5 |

Or pass `--frame-u-factor` with a manufacturer-supplied NFRC/CSA number.

## Usage

```bash
python3 -m window_frame_temp --frame standard_vinyl --storey 1
python3 -m window_frame_temp --frame foam_filled_vinyl --storey 6
python3 -m window_frame_temp --frame-u-factor 1.8 --storey 4 --indoor-rh 40

# Winter condensation check, sunny south elevation (partially offsets condensation risk)
python3 -m window_frame_temp --storey 6 --orientation S --solar-scenario winter_sunny

# Summer overheating/warping check, west elevation, black frame
python3 -m window_frame_temp --storey 4 --orientation W --frame-colour black \
    --solar-scenario summer_peak --indoor-temp 24 --indoor-rh 45 --outdoor-temp 28 --wind-speed 2.0
```

`--storey` must be between 1 and 6, matching the six-storey building this
tool targets.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

- 1D lumped resistance only; does not capture 2D heat flow around glazing
  edge spacers, corners, or fasteners (use THERM/NFRC simulation for
  certification-grade numbers).
- Assumes steady-state conditions, not transient response to weather swings.
- Indoor film coefficient is held constant; only the exterior film responds
  to wind/height.
