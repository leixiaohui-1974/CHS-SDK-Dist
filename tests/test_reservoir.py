import unittest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.physical_objects.reservoir import Reservoir

class TestReservoir(unittest.TestCase):
    """
    Unit tests for the Reservoir physical component.
    """

    def setUp(self):
        """Set up a new reservoir for each test."""
        self.initial_state = {'water_level': 10.0, 'volume': 10000.0}
        self.parameters = {'surface_area': 1000.0} # V = A * h
        self.reservoir = Reservoir(
            name="test_reservoir",
            initial_state=self.initial_state,
            parameters=self.parameters
        )

    def test_initialization(self):
        """Test that the reservoir is initialized correctly."""
        state = self.reservoir.get_state()
        self.assertEqual(self.reservoir.name, "test_reservoir")
        self.assertEqual(state['water_level'], 10.0)
        self.assertEqual(state['volume'], 10000.0)

    def test_water_balance_positive_net_inflow(self):
        """Test the water balance equation with a net inflow."""
        dt = 60.0  # 60 seconds

        # Manually set the inflow from upstream components
        self.reservoir.set_inflow(10.0) # m^3/s

        # The action dictionary specifies the outflow demanded by downstream
        action = {'outflow': 5.0} # m^3/s

        # The net flow is 10 - 5 = 5 m^3/s
        # Change in volume = 5 m^3/s * 60 s = 300 m^3
        expected_new_volume = 10000.0 + 300.0
        expected_new_water_level = expected_new_volume / self.parameters['surface_area']

        # Step the simulation
        new_state = self.reservoir.step(action, dt)

        self.assertAlmostEqual(new_state['volume'], expected_new_volume)
        self.assertAlmostEqual(new_state['water_level'], expected_new_water_level)

    def test_water_balance_negative_net_inflow(self):
        """Test the water balance equation with a net outflow."""
        dt = 100.0 # 100 seconds

        self.reservoir.set_inflow(2.0) # m^3/s
        action = {'outflow': 8.0} # m^3/s

        # Net flow is 2 - 8 = -6 m^3/s
        # Change in volume = -6 m^3/s * 100 s = -600 m^3
        expected_new_volume = 10000.0 - 600.0
        expected_new_water_level = expected_new_volume / self.parameters['surface_area']

        new_state = self.reservoir.step(action, dt)

        self.assertAlmostEqual(new_state['volume'], expected_new_volume)
        self.assertAlmostEqual(new_state['water_level'], expected_new_water_level)

    def test_data_inflow_message(self):
        """Test that the reservoir correctly handles data-driven inflow via messages."""
        # This requires a message bus, which we'll simulate here.
        # In a real test, you might use a mock message bus.
        from core_lib.central_coordination.collaboration.message_bus import MessageBus
        bus = MessageBus()

        # Re-initialize reservoir with a bus and topic
        self.reservoir = Reservoir(
            name="test_reservoir_with_bus",
            initial_state=self.initial_state,
            parameters=self.parameters,
            message_bus=bus,
            inflow_topic="inflow/test"
        )

        # Simulate a message being published
        bus.publish("inflow/test", {'inflow_rate': 3.0})

        dt = 10.0
        self.reservoir.set_inflow(5.0) # Physical inflow
        action = {'outflow': 4.0} # Outflow demand

        # Net flow should be (physical + data) - outflow = (5 + 3) - 4 = 4 m^3/s
        # Change in volume = 4 m^3/s * 10 s = 40 m^3
        expected_new_volume = 10000.0 + 40.0

        new_state = self.reservoir.step(action, dt)
        self.assertAlmostEqual(new_state['volume'], expected_new_volume)


if __name__ == '__main__':
    unittest.main()
