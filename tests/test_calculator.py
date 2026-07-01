import math
import unittest

from window_frame_temp.calculator import compute_frame_temperature
from window_frame_temp.climate import VANCOUVER_WINTER_DESIGN, dew_point_c
from window_frame_temp.frame import FrameProfile, get_frame_profile
from window_frame_temp.wind import exterior_film_coefficient, wind_speed_at_storey


class DewPointTests(unittest.TestCase):
    def test_100_percent_rh_equals_air_temp(self):
        self.assertAlmostEqual(dew_point_c(20.0, 100.0), 20.0, places=6)

    def test_lower_rh_gives_lower_dew_point(self):
        self.assertLess(dew_point_c(21.0, 30.0), dew_point_c(21.0, 60.0))

    def test_rejects_invalid_rh(self):
        with self.assertRaises(ValueError):
            dew_point_c(20.0, 0.0)
        with self.assertRaises(ValueError):
            dew_point_c(20.0, 101.0)


class WindTests(unittest.TestCase):
    def test_wind_speed_increases_with_storey(self):
        self.assertLess(
            wind_speed_at_storey(3.6, 1), wind_speed_at_storey(3.6, 6)
        )

    def test_rejects_storey_below_one(self):
        with self.assertRaises(ValueError):
            wind_speed_at_storey(3.6, 0)

    def test_film_coefficient_increases_with_wind(self):
        self.assertLess(
            exterior_film_coefficient(1.0), exterior_film_coefficient(10.0)
        )


class FramePresetTests(unittest.TestCase):
    def test_better_frame_has_higher_resistance(self):
        standard = get_frame_profile("standard_vinyl")
        foam_filled = get_frame_profile("foam_filled_vinyl")
        self.assertGreater(
            foam_filled.conductive_resistance_m2k_w,
            standard.conductive_resistance_m2k_w,
        )

    def test_unknown_preset_raises(self):
        with self.assertRaises(ValueError):
            get_frame_profile("aluminum")


class ComputeFrameTemperatureTests(unittest.TestCase):
    def test_frame_temp_between_indoor_and_outdoor(self):
        frame = get_frame_profile("standard_vinyl")
        result = compute_frame_temperature(frame, storey=1)
        self.assertGreater(result.interior_surface_temp_c, VANCOUVER_WINTER_DESIGN.outdoor_temp_c)
        self.assertLess(result.interior_surface_temp_c, VANCOUVER_WINTER_DESIGN.indoor_temp_c)
        self.assertGreater(result.exterior_surface_temp_c, VANCOUVER_WINTER_DESIGN.outdoor_temp_c)
        self.assertLess(result.exterior_surface_temp_c, VANCOUVER_WINTER_DESIGN.indoor_temp_c)

    def test_better_insulated_frame_is_warmer_inside(self):
        standard = get_frame_profile("standard_vinyl")
        foam_filled = get_frame_profile("foam_filled_vinyl")
        result_standard = compute_frame_temperature(standard, storey=1)
        result_foam = compute_frame_temperature(foam_filled, storey=1)
        self.assertGreater(
            result_foam.interior_surface_temp_c, result_standard.interior_surface_temp_c
        )

    def test_higher_storey_is_colder_on_interior_surface(self):
        frame = get_frame_profile("standard_vinyl")
        low = compute_frame_temperature(frame, storey=1)
        high = compute_frame_temperature(frame, storey=6)
        self.assertLess(high.interior_surface_temp_c, low.interior_surface_temp_c)

    def test_temperature_index_is_between_0_and_100(self):
        frame = get_frame_profile("standard_vinyl")
        result = compute_frame_temperature(frame, storey=1)
        self.assertTrue(0.0 <= result.temperature_index_pct <= 100.0)

    def test_condensation_flagged_when_surface_colder_than_dew_point(self):
        from window_frame_temp.climate import ClimateDesignPoint

        # 30% design RH keeps vinyl frames safely above dew point by design;
        # a humid interior (e.g. bathroom/kitchen at 50% RH) with a poor
        # frame is what actually pushes the surface below dew point.
        humid_climate = ClimateDesignPoint(
            indoor_temp_c=21.0, indoor_rh_pct=50.0, outdoor_temp_c=-7.1, wind_speed_mps=3.6
        )
        frame = FrameProfile(name="poor_vinyl", nfrc_u_factor_w_m2k=6.0)
        result = compute_frame_temperature(frame, storey=1, climate=humid_climate)
        self.assertTrue(result.condensation_risk)
        self.assertLessEqual(result.interior_surface_temp_c, result.indoor_dew_point_c)

    def test_zero_indoor_outdoor_span_gives_full_index(self):
        from window_frame_temp.climate import ClimateDesignPoint

        frame = get_frame_profile("standard_vinyl")
        climate = ClimateDesignPoint(
            indoor_temp_c=10.0, indoor_rh_pct=50.0, outdoor_temp_c=10.0, wind_speed_mps=3.6
        )
        result = compute_frame_temperature(frame, storey=1, climate=climate)
        self.assertTrue(math.isclose(result.interior_surface_temp_c, 10.0, abs_tol=1e-6))


if __name__ == "__main__":
    unittest.main()
