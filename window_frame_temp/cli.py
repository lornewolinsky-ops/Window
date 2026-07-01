"""Command-line interface for the vinyl window frame temperature calculator."""

import argparse
import sys

from .calculator import compute_frame_temperature
from .climate import ClimateDesignPoint, VANCOUVER_WINTER_DESIGN
from .frame import FRAME_PRESETS_NFRC_U_FACTOR, FrameProfile, get_frame_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the steady-state surface temperature of a vinyl window "
            "frame in a wood-frame residential building, defaulting to "
            "Vancouver winter design conditions."
        )
    )
    parser.add_argument(
        "--frame",
        choices=sorted(FRAME_PRESETS_NFRC_U_FACTOR),
        default="standard_vinyl",
        help="Vinyl frame preset (default: standard_vinyl)",
    )
    parser.add_argument(
        "--frame-u-factor",
        type=float,
        default=None,
        help="Override the frame preset with a custom NFRC-style whole-frame "
        "U-factor in W/m^2K",
    )
    parser.add_argument(
        "--storey",
        type=int,
        default=1,
        help="Storey number (1-6) used to estimate wind exposure at height (default: 1)",
    )
    parser.add_argument("--indoor-temp", type=float, default=VANCOUVER_WINTER_DESIGN.indoor_temp_c,
                         help="Indoor air temperature in C")
    parser.add_argument("--indoor-rh", type=float, default=VANCOUVER_WINTER_DESIGN.indoor_rh_pct,
                         help="Indoor relative humidity in %%")
    parser.add_argument("--outdoor-temp", type=float, default=VANCOUVER_WINTER_DESIGN.outdoor_temp_c,
                         help="Outdoor air temperature in C")
    parser.add_argument("--wind-speed", type=float, default=VANCOUVER_WINTER_DESIGN.wind_speed_mps,
                         help="Reference (10 m) wind speed in m/s")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.storey < 1 or args.storey > 6:
        parser.error("--storey must be between 1 and 6 for this six-storey building model")

    if args.frame_u_factor is not None:
        frame = FrameProfile(name="custom", nfrc_u_factor_w_m2k=args.frame_u_factor)
    else:
        frame = get_frame_profile(args.frame)

    climate = ClimateDesignPoint(
        indoor_temp_c=args.indoor_temp,
        indoor_rh_pct=args.indoor_rh,
        outdoor_temp_c=args.outdoor_temp,
        wind_speed_mps=args.wind_speed,
    )

    result = compute_frame_temperature(frame, storey=args.storey, climate=climate)

    print(f"Frame: {frame.name} (NFRC U-factor {frame.nfrc_u_factor_w_m2k:.2f} W/m^2K)")
    print(f"Storey: {args.storey}")
    print(f"Indoor: {climate.indoor_temp_c:.1f} C @ {climate.indoor_rh_pct:.0f}% RH")
    print(f"Outdoor: {climate.outdoor_temp_c:.1f} C, reference wind {climate.wind_speed_mps:.1f} m/s")
    print("-" * 50)
    print(f"Interior frame surface temperature: {result.interior_surface_temp_c:.1f} C")
    print(f"Exterior frame surface temperature: {result.exterior_surface_temp_c:.1f} C")
    print(f"Indoor dew point:                   {result.indoor_dew_point_c:.1f} C")
    print(f"Actual assembly U-factor:           {result.u_factor_actual_w_m2k:.2f} W/m^2K")
    print(f"Heat flux:                          {result.heat_flux_w_m2:.1f} W/m^2")
    print(f"Temperature index (CSA A440-style): {result.temperature_index_pct:.0f}%")
    print(f"Condensation risk on frame:         {'YES' if result.condensation_risk else 'no'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
