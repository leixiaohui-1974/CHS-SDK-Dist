import unittest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationLoader
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

class TestYamlLoader(unittest.TestCase):
    """
    Tests the functionality of the SimulationLoader to ensure it can
    correctly parse YAML files and build a simulation harness.
    """

    def test_load_yinchuojiliao_scenario(self):
        """
        Tests loading the full yinchuojiliao scenario.
        This acts as an integration test for the loading process.
        """
        scenario_path = project_root / "mission" / "scenarios" / "yinchuojiliao"
        self.assertTrue(scenario_path.is_dir(), f"Scenario directory not found at {scenario_path}")

        loader = SimulationLoader(scenario_path=str(scenario_path))
        harness = loader.load()

        # 1. Check if the harness was created
        self.assertIsInstance(harness, SimulationHarness)

        # 2. Check if components were loaded (based on our YAML files)
        # 13 components in components.yml
        self.assertEqual(len(harness.components), 13)
        self.assertIn("wendegen_reservoir", harness.components)
        self.assertIn("terminal_pool", harness.components)

        # 3. Check if agents and controllers were loaded
        # 5 controllers + 16 agents = 21 total agents/controllers in the harness list
        # Note: The harness stores controllers and agents in different internal lists.
        # Let's check them separately. 5 controllers, 16 agents.
        self.assertEqual(len(harness.controllers), 5)
        self.assertEqual(len(harness.agents), 16) # 13 twins + 3 custom agents

        # 4. Check if the topology was built
        # The harness should have a sorted component list after build() is called.
        self.assertTrue(len(harness.sorted_components) > 0)
        self.assertEqual(len(harness.sorted_components), 13)


if __name__ == '__main__':
    unittest.main()
