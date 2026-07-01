"""Vinyl window frame thermal properties."""

from dataclasses import dataclass

# NFRC/CSA-A440 whole-frame U-factors (W/m^2K) are simulated/measured with the
# standard NFRC 100 boundary films baked in (Rsi=0.1206, Rso=0.0385 m^2K/W).
# To recombine the frame with actual site film coefficients we first strip
# those standard films out to get the frame's own conductive resistance.
NFRC_STANDARD_RSI = 0.1206
NFRC_STANDARD_RSO = 0.0385

FRAME_PRESETS_NFRC_U_FACTOR = {
    "standard_vinyl": 2.5,       # single/dual hollow-chamber vinyl, no foam fill
    "multi_chamber_vinyl": 2.0,  # multi-chamber vinyl, no foam fill
    "foam_filled_vinyl": 1.5,    # foam-filled multi-chamber, thermally improved
}


@dataclass(frozen=True)
class FrameProfile:
    name: str
    nfrc_u_factor_w_m2k: float

    @property
    def conductive_resistance_m2k_w(self) -> float:
        """R-value of the frame material alone, with standard NFRC films removed."""
        r_total = 1.0 / self.nfrc_u_factor_w_m2k
        r_material = r_total - NFRC_STANDARD_RSI - NFRC_STANDARD_RSO
        if r_material <= 0:
            raise ValueError(
                f"NFRC U-factor {self.nfrc_u_factor_w_m2k} implies non-physical "
                "frame resistance once standard surface films are removed"
            )
        return r_material


def get_frame_profile(name: str) -> FrameProfile:
    try:
        u_factor = FRAME_PRESETS_NFRC_U_FACTOR[name]
    except KeyError as exc:
        valid = ", ".join(sorted(FRAME_PRESETS_NFRC_U_FACTOR))
        raise ValueError(f"Unknown frame preset '{name}'. Valid options: {valid}") from exc
    return FrameProfile(name=name, nfrc_u_factor_w_m2k=u_factor)
