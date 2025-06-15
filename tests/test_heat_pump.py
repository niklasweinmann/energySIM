"""
Tests für die Wärmepumpen-Simulation.
"""

import unittest

import numpy as np

from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications


class TestHeatPump(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit einer typischen Luft-Wasser-Wärmepumpe."""
        # COP-Werte nach VDI 4645
        cop_rating_points = {
            (-7, 35): 2.70,  # Außentemp, Vorlauftemp
            (-7, 45): 2.20,
            (2, 35): 3.40,
            (2, 45): 2.70,
            (7, 35): 4.00,
            (7, 45): 3.20,
            (10, 35): 4.40,
            (10, 45): 3.50,
        }

        self.specs = HeatPumpSpecifications(
            nominal_heating_power=10.0,  # 10 kW
            cop_rating_points=cop_rating_points,
            min_outside_temp=-20.0,
            max_flow_temp=60.0,
            min_part_load_ratio=0.3,
            defrost_temp_threshold=7.0,
            thermal_mass=20.0,
        )

        self.heat_pump = HeatPump(self.specs)

    def test_cop_calculation(self):
        """Test der COP-Berechnung."""
        # Test bei Normbedingungen (A7/W35)
        cop = self.heat_pump.calculate_cop(7.0, 35.0)
        self.assertAlmostEqual(cop, 4.0, places=2)

        # Test bei Interpolation zwischen A2W35 (3.4) und A2W45 (2.7)
        cop = self.heat_pump.calculate_cop(2.0, 40.0)
        print(f"\nBerechneter COP bei A2/W40: {cop}")  # Debug-Ausgabe
        self.assertTrue(2.7 < cop < 3.4, f"COP {cop} liegt nicht zwischen 2.7 und 3.4")

        # Test bei niedrigen Temperaturen mit Abtauung
        cop_with_defrost = self.heat_pump.calculate_cop(2.0, 35.0)
        cop_without_defrost = self.heat_pump.calculate_cop(12.0, 35.0)
        self.assertLess(cop_with_defrost, cop_without_defrost)

    def test_power_output(self):
        """Test der Leistungsberechnung."""
        # Test bei Volllast
        heat_output, power_input = self.heat_pump.get_power_output(
            outside_temp=7.0, flow_temp=35.0, demand=10.0, time_step=1.0  # 10 kWh
        )

        self.assertAlmostEqual(heat_output, 10.0, places=1)
        self.assertAlmostEqual(power_input, 10.0 / 4.0, places=1)  # COP = 4.0

        # Test bei Teillast
        heat_output, power_input = self.heat_pump.get_power_output(
            outside_temp=7.0, flow_temp=35.0, demand=2.0, time_step=1.0  # 2 kWh
        )

        min_power = 10.0 * 0.3  # Minimale Leistung
        self.assertGreaterEqual(heat_output, 2.0)
        self.assertLess(heat_output, min_power * 1.1)

    def test_flow_temperature(self):
        """Test der Vorlauftemperaturberechnung."""
        # Test bei verschiedenen Außentemperaturen
        temps = [-15, -10, -5, 0, 5, 10, 15]
        flow_temps = [self.heat_pump.calculate_flow_temperature(t) for t in temps]

        # Temperaturen sollten mit steigender Außentemperatur fallen
        for t1, t2 in zip(flow_temps[:-1], flow_temps[1:]):
            self.assertGreater(t1, t2)

        # Vorlauftemperatur sollte Maximaltemperatur nicht überschreiten
        self.assertTrue(all(t <= self.specs.max_flow_temp for t in flow_temps))

    def test_defrost_operation(self):
        """Test des Abtaubetriebs."""
        # Betrieb ohne Abtauung
        _, power_no_defrost = self.heat_pump.get_power_output(
            outside_temp=10.0, flow_temp=35.0, demand=5.0
        )

        # Betrieb mit Abtauung
        _, power_with_defrost = self.heat_pump.get_power_output(
            outside_temp=2.0, flow_temp=35.0, demand=5.0
        )

        # Abtaubetrieb sollte mehr Energie benötigen
        self.assertGreater(power_with_defrost, power_no_defrost)

    def test_operating_limits(self):
        """Test der Betriebsgrenzen."""
        # Test unterhalb der minimalen Außentemperatur
        heat_output, power_input = self.heat_pump.get_power_output(
            outside_temp=self.specs.min_outside_temp - 1, flow_temp=35.0, demand=5.0
        )
        self.assertEqual(heat_output, 0.0)
        self.assertEqual(power_input, 0.0)

        # Test oberhalb der maximalen Vorlauftemperatur
        heat_output, power_input = self.heat_pump.get_power_output(
            outside_temp=7.0, flow_temp=self.specs.max_flow_temp + 1, demand=5.0
        )
        self.assertEqual(heat_output, 0.0)
        self.assertEqual(power_input, 0.0)


if __name__ == "__main__":
    unittest.main()
