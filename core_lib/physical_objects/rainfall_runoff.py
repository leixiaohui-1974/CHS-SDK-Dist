"""
Simulation model for a Rainfall-Runoff process.
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class RainfallRunoff(PhysicalObjectInterface):
    """
    Represents a rainfall-runoff process for a catchment area.

    This model converts rainfall intensity into a flow rate (runoff). It subscribes
    to a topic on the message bus to get rainfall data. The generated runoff is
    treated as the outflow of this component, which can then be connected to
    another component (e.g., a reservoir or river channel) as an inflow.
    """

    def __init__(self, name: str, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, rainfall_topic: Optional[str] = None):
        """
        Initializes the RainfallRunoff model.

        Args:
            name: The unique name for this component.
            parameters: A dictionary containing the model parameters:
                - catchment_area: The area of the catchment in square meters (m^2).
                - runoff_coefficient: A dimensionless factor representing the fraction
                                      of rainfall that becomes runoff (0 to 1).
            message_bus: The system's message bus.
            rainfall_topic: The topic to subscribe to for rainfall data. The message
                            is expected to have a 'rainfall_intensity' key in m/s.
        """
        # This component is stateless, so initial_state is empty.
        super().__init__(name, initial_state={}, parameters=parameters)
        self.bus = message_bus
        self.rainfall_topic = rainfall_topic
        self.rainfall_intensity = 0.0  # m/s

        if self.bus and self.rainfall_topic:
            self.bus.subscribe(self.rainfall_topic, self.handle_rainfall_message)
            print(f"RainfallRunoff model '{self.name}' subscribed to rainfall topic '{self.rainfall_topic}'.")

    def handle_rainfall_message(self, message: Message):
        """Callback to handle incoming rainfall data messages."""
        intensity = message.get('rainfall_intensity')
        if isinstance(intensity, (int, float)):
            self.rainfall_intensity = intensity  # m/s

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Calculates the runoff for a single time step.

        The runoff is calculated using the Rational Method formula:
        Q = C * i * A
        where:
        Q = runoff flow rate (m^3/s)
        C = runoff coefficient
        i = rainfall intensity (m/s)
        A = catchment area (m^2)
        """
        catchment_area = self._params.get('catchment_area')
        runoff_coefficient = self._params.get('runoff_coefficient')

        if catchment_area is None or runoff_coefficient is None:
            raise ValueError("Parameters 'catchment_area' and 'runoff_coefficient' must be defined.")

        # Calculate runoff
        runoff_m3_per_s = runoff_coefficient * self.rainfall_intensity * catchment_area

        # The generated runoff is the outflow of this component.
        self._state['outflow'] = runoff_m3_per_s

        # Reset rainfall intensity for the next step to ensure that if no new
        # message arrives, the rainfall is considered to be zero.
        self.rainfall_intensity = 0.0

        return self._state

    @property
    def is_stateful(self) -> bool:
        # This model's output depends only on the current input (rainfall),
        # not on past states. Therefore, it is stateless.
        return False

    def set_parameters(self, parameters: Parameters):
        """Allows updating the model's parameters."""
        self._params.update(parameters)
        print(f"[{self.name}] Parameters updated: {parameters}")

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """
        Identifies the runoff_coefficient parameter from data.

        Args:
            data: A dictionary containing 'rainfall' and 'observed_runoff' numpy arrays.
            method: The identification method (currently only 'offline' is supported).

        Returns:
            A dictionary with the identified parameter.
        """
        if method != 'offline':
            raise NotImplementedError("Only 'offline' identification is currently supported.")

        rainfall_series = data['rainfall']
        observed_runoff = data['observed_runoff']

        def objective_func(param_to_optimize):
            """The function to minimize: RMSE between simulated and observed runoff."""
            test_coeff = param_to_optimize[0]

            # Simulate runoff with the test coefficient
            catchment_area = self._params['catchment_area']
            simulated_runoff = test_coeff * rainfall_series * catchment_area

            # Calculate RMSE
            rmse = np.sqrt(np.mean((simulated_runoff - observed_runoff) ** 2))
            return rmse

        # Initial guess for the runoff coefficient
        initial_guess = [self._params.get('runoff_coefficient', 0.5)]

        # Bounds for the coefficient (0 to 1)
        bnds = [(0.0, 1.0)]

        # Run the optimization
        result = minimize(
            objective_func,
            initial_guess,
            method='SLSQP',
            bounds=bnds
        )

        if result.success:
            identified_coeff = result.x[0]
            print(f"[{self.name}] Parameter identification successful. Identified runoff_coefficient: {identified_coeff:.4f}")
            new_params = {'runoff_coefficient': identified_coeff}
            self.set_parameters(new_params)
            return new_params
        else:
            print(f"[{self.name}] WARNING: Parameter identification failed. Reason: {result.message}")
            return self.get_parameters()
