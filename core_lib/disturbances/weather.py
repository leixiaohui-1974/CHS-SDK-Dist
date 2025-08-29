"""
Disturbance model for weather phenomena.
"""
from typing import Dict, Any
from core_lib.core.interfaces import Disturbance

class WeatherDisturbance(Disturbance):
    """
    Represents weather-related disturbances, such as rainfall or evaporation.

    This class can be used by the simulation environment to introduce
    unplanned inflows (rain) or losses (evaporation) to the water system,
    allowing for more realistic testing of control strategies.
    """

    def __init__(self, disturbance_id: str):
        self.disturbance_id = disturbance_id
        print(f"WeatherDisturbance model '{self.disturbance_id}' created.")

    def get_disturbance(self, time: float) -> Dict[str, Any]:
        """
        Generates a weather disturbance value for a given time.

        A real implementation might read from a historical weather dataset
        or use a stochastic weather generator.

        Args:
            time: The simulation time.

        Returns:
            A dictionary of disturbances, e.g., {'rainfall_rate': 0.001}.
        """
        # Placeholder logic: simple sinusoidal rainfall pattern for testing
        import math
        # Simulate a daily rainfall cycle
        rainfall_rate = 0.0005 * (1 + math.sin(2 * math.pi * time / 86400)) # m/s, very light drizzle
        return {'rainfall_rate': rainfall_rate}
