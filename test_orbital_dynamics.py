"""Analytic references and convergence gates for the new numerical engine."""
import json
import math
import unittest

from orbital_dynamics import G, YEAR_DAYS, build_experiment, integrate, orbit_elements, validate_settings


class OrbitalPhysicsTests(unittest.TestCase):
    def test_current_earth_reference(self):
        e = orbit_elements(1)
        self.assertEqual(e['state'], 'circle')
        self.assertAlmostEqual(e['period_days'], YEAR_DAYS)
        self.assertAlmostEqual(e['velocity_kms'], 29.785, places=2)
        self.assertAlmostEqual(e['semimajor_au'], 1)

    def test_sudden_twenty_percent_mass_loss(self):
        e = orbit_elements(.8)
        self.assertAlmostEqual(e['eccentricity'], .25)
        self.assertAlmostEqual(e['semimajor_au'], 4 / 3)
        self.assertAlmostEqual(e['perihelion_au'], 1)
        self.assertAlmostEqual(e['aphelion_au'], 5 / 3)
        self.assertAlmostEqual(e['period_days'], math.sqrt((4 / 3)**3 / .8) * YEAR_DAYS)

    def test_escape_boundary_and_neighboring_masses(self):
        for mass, state, bound in [(.499, 'hyperbola', False), (.5, 'parabola', False), (.501, 'ellipse', True)]:
            with self.subTest(mass=mass):
                e = orbit_elements(mass)
                self.assertEqual(e['state'], state)
                self.assertEqual(e['bound'], bound)
                if not bound:
                    self.assertIsNone(e['period_days'])
                    self.assertIsNone(e['aphelion_au'])
        self.assertAlmostEqual(orbit_elements(.5)['energy_km2_s2'], 0)

    def test_increased_mass_starts_at_aphelion(self):
        e = orbit_elements(2)
        self.assertAlmostEqual(e['eccentricity'], .5)
        self.assertAlmostEqual(e['aphelion_au'], 1)
        self.assertAlmostEqual(e['perihelion_au'], 1 / 3)

    def test_circular_kepler_scaling_for_radius_and_mass(self):
        for mass, radius in [(.2, .5), (.8, 1), (2, 2), (1, 1.5)]:
            with self.subTest(mass=mass, radius=radius):
                e = orbit_elements(mass, radius, 'circular')
                self.assertEqual(e['eccentricity'], 0)
                self.assertAlmostEqual((e['period_days'] / YEAR_DAYS)**2, radius**3 / mass)

    def test_position_and_period_match_analytic_orbit(self):
        e = orbit_elements(.8)
        result = integrate(.8, step_days=.25, duration_years=e['period_days'] / YEAR_DAYS)
        _, x, y = result['trajectory'][-1]
        self.assertLess(math.hypot(x - 1, y), .0002)
        radii = [math.hypot(p[1], p[2]) for p in result['trajectory']]
        self.assertAlmostEqual(max(radii), e['aphelion_au'], places=3)

    def test_verlet_second_order_energy_convergence(self):
        coarse = integrate(.8, step_days=2)['max_energy_error_pct']
        fine = integrate(.8, step_days=1)['max_energy_error_pct']
        self.assertGreater(coarse / fine, 3.8)
        self.assertLess(coarse / fine, 4.2)

    def test_angular_momentum_is_preserved(self):
        self.assertLess(integrate(.8)['max_momentum_error_pct'], 1e-9)

    def test_parabolic_normalization_is_finite(self):
        data = build_experiment({'mass': .5})
        self.assertTrue(math.isfinite(data['simulation']['max_energy_error_pct']))
        json.dumps(data, allow_nan=False)

    def test_invalid_input_is_rejected(self):
        for values in [{'mass': math.nan}, {'mass': math.inf}, {'mass': True}, {'mass': 0}, {'radius': -.5}, {'step': 0}, {'model': 'adiabatic'}, 'invalid', [], '', False]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_settings(values)

    def test_full_ui_parameter_range_produces_finite_json(self):
        for mass in [.2, .5, .51, .8, 1, 1.5, 2]:
            for radius in [.5, 1, 2]:
                for model in ['impulse', 'circular']:
                    with self.subTest(mass=mass, radius=radius, model=model):
                        data = build_experiment({'mass': mass, 'radius': radius, 'model': model, 'step': 4})
                        json.dumps(data, allow_nan=False)
                        self.assertEqual(len(data['simulation']['trajectory']), len(data['simulation']['diagnostics']))

    def test_learner_explanation_matches_orbit_classification(self):
        for mass, shape in [(1, 'circle'), (.8, 'ellipse'), (1.5, 'ellipse'), (.5, 'escape'), (.4, 'escape')]:
            with self.subTest(mass=mass):
                data = build_experiment({'mass': mass})
                learning = data['learning']
                self.assertEqual(learning['shape'], shape)
                self.assertEqual(learning['mass_percent'], round(mass * 100))
                if shape == 'escape':
                    self.assertIsNone(learning['period_days_rounded'])
                    self.assertIn('한 바퀴 돌지', learning['period_text'])
                    self.assertNotIn('일이 걸렸다', learning['observation_starter'])
                else:
                    self.assertEqual(learning['period_days_rounded'], round(data['elements']['period_days']))

    def test_learner_explanation_respects_circular_initial_speed(self):
        data = build_experiment({'mass': .5, 'model': 'circular', 'radius': 1.5})
        self.assertEqual(data['learning']['shape'], 'circle')
        self.assertEqual(data['learning']['radius_percent'], 150)
        self.assertIn('맞는 속도', data['learning']['reason'])
        self.assertNotIn('떠나는', data['learning']['headline'])
        self.assertIn('출발', data['learning']['model_note'])


if __name__ == '__main__':
    unittest.main()
