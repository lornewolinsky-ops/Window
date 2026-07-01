"""Minimal browser front end for the vinyl window frame temperature calculator.

Pure stdlib (no Flask dependency) -- a single form page that reuses the same
window_frame_temp.compute_frame_temperature() used by the CLI, so the physics
lives in exactly one place.
"""

import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from window_frame_temp import ClimateDesignPoint, FRAME_PRESETS_NFRC_U_FACTOR, VANCOUVER_WINTER_DESIGN
from window_frame_temp.calculator import compute_frame_temperature
from window_frame_temp.frame import FrameProfile, get_frame_profile
from window_frame_temp.solar import (
    FRAME_COLOR_SOLAR_ABSORPTIVITY,
    ORIENTATIONS,
    SOLAR_IRRADIANCE_TABLE_W_M2,
)

DEFAULTS = {
    "frame": "standard_vinyl",
    "storey": "1",
    "orientation": "S",
    "frame_colour": "white",
    "solar_scenario": "winter_design",
    "indoor_temp": str(VANCOUVER_WINTER_DESIGN.indoor_temp_c),
    "indoor_rh": str(VANCOUVER_WINTER_DESIGN.indoor_rh_pct),
    "outdoor_temp": str(VANCOUVER_WINTER_DESIGN.outdoor_temp_c),
    "wind_speed": str(VANCOUVER_WINTER_DESIGN.wind_speed_mps),
}


def select(name: str, options, current: str) -> str:
    opts = "\n".join(
        f'<option value="{o}"{" selected" if o == current else ""}>{o}</option>' for o in options
    )
    return f'<select name="{name}">{opts}</select>'


def render_page(params: dict) -> str:
    values = {**DEFAULTS, **params}

    frame = get_frame_profile(values["frame"])
    climate = ClimateDesignPoint(
        indoor_temp_c=float(values["indoor_temp"]),
        indoor_rh_pct=float(values["indoor_rh"]),
        outdoor_temp_c=float(values["outdoor_temp"]),
        wind_speed_mps=float(values["wind_speed"]),
    )
    result = compute_frame_temperature(
        frame,
        storey=int(values["storey"]),
        climate=climate,
        orientation=values["orientation"],
        frame_color=values["frame_colour"],
        solar_scenario=values["solar_scenario"],
    )

    def num(name, label, step="0.1"):
        v = html.escape(values[name])
        return (
            f'<label>{label}<br>'
            f'<input type="number" step="{step}" name="{name}" value="{v}"></label>'
        )

    storey_options = [str(s) for s in range(1, 7)]

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Vinyl Window Frame Temperature Calculator</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  form {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem 1.5rem; margin-bottom: 1.5rem; }}
  label {{ font-size: 0.85rem; color: #444; }}
  input, select {{ width: 100%; padding: 0.35rem; box-sizing: border-box; }}
  button {{ grid-column: span 2; padding: 0.6rem; font-size: 1rem; cursor: pointer; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td {{ padding: 0.35rem 0.5rem; border-bottom: 1px solid #eee; }}
  td:first-child {{ color: #444; }}
  td:last-child {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .risk-yes {{ color: #b00020; font-weight: 600; }}
  .risk-no {{ color: #1a7a1a; }}
</style>
</head>
<body>
<h1>Vinyl Window Frame Temperature Calculator</h1>
<p>Six-storey wood-frame residential building, Vancouver BC. Defaults are the winter design condition.</p>
<form method="get" action="/">
  <label>Frame preset<br>{select("frame", sorted(FRAME_PRESETS_NFRC_U_FACTOR), values["frame"])}</label>
  <label>Storey<br>{select("storey", storey_options, values["storey"])}</label>
  <label>Orientation<br>{select("orientation", ORIENTATIONS, values["orientation"])}</label>
  <label>Frame colour<br>{select("frame_colour", sorted(FRAME_COLOR_SOLAR_ABSORPTIVITY), values["frame_colour"])}</label>
  <label>Solar scenario<br>{select("solar_scenario", sorted(SOLAR_IRRADIANCE_TABLE_W_M2), values["solar_scenario"])}</label>
  <span></span>
  {num("indoor_temp", "Indoor temp (C)")}
  {num("indoor_rh", "Indoor RH (%)")}
  {num("outdoor_temp", "Outdoor temp (C)")}
  {num("wind_speed", "Reference wind speed (m/s)")}
  <button type="submit">Calculate</button>
</form>
<table>
  <tr><td>Interior frame surface temperature</td><td>{result.interior_surface_temp_c:.1f} &deg;C</td></tr>
  <tr><td>Exterior frame surface temperature</td><td>{result.exterior_surface_temp_c:.1f} &deg;C</td></tr>
  <tr><td>Sol-air temperature</td><td>{result.sol_air_temp_c:.1f} &deg;C ({result.solar_irradiance_w_m2:.0f} W/m&sup2; incident)</td></tr>
  <tr><td>Indoor dew point</td><td>{result.indoor_dew_point_c:.1f} &deg;C</td></tr>
  <tr><td>Actual assembly U-factor</td><td>{result.u_factor_actual_w_m2k:.2f} W/m&sup2;K</td></tr>
  <tr><td>Heat flux</td><td>{result.heat_flux_w_m2:.1f} W/m&sup2;</td></tr>
  <tr><td>Temperature index (CSA A440-style)</td><td>{result.temperature_index_pct:.0f}%</td></tr>
  <tr><td>Condensation risk on frame</td><td class="{'risk-yes' if result.condensation_risk else 'risk-no'}">{"YES" if result.condensation_risk else "no"}</td></tr>
  <tr><td>Frame heat distortion risk</td><td class="{'risk-yes' if result.frame_distortion_risk else 'risk-no'}">{"YES" if result.frame_distortion_risk else "no"}</td></tr>
</table>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            body = render_page(params).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, KeyError) as exc:
            body = f"<p>Invalid input: {html.escape(str(exc))}</p>".encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def main(port: int = 8000):
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
