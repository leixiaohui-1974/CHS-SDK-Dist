"""
A Proportional-Integral-Derivative (PID) Controller with anti-windup.
"""
from core_lib.core.interfaces import Controller, State

class PIDController(Controller):
    """
    A standard PID controller with clamping and anti-windup.

    This controller computes an action based on the error between a setpoint and a
    process variable. It includes an anti-windup mechanism to prevent integral
    term saturation when the actuator is at its limit.
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float,
                 min_output: float, max_output: float):
        """
        Initializes the PID controller.

        Args:
            Kp: Proportional gain.
            Ki: Integral gain.
            Kd: Derivative gain.
            setpoint: The desired value for the system state.
            min_output: The minimum value for the control action.
            max_output: The maximum value for the control action.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.min_output = min_output
        self.max_output = max_output

        self._integral = 0
        self._previous_error = 0
        print(f"PIDController created with Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}, "
              f"OutputRange=[{min_output}, {max_output}].")

    def compute_control_action(self, observation: State, dt: float) -> float:
        """
        Computes the PID control action with anti-windup.

        Args:
            observation: The current state, must contain the key 'process_variable'.
            dt: The time step duration in seconds.

        Returns:
            The computed and clamped control action.
        """
        if dt <= 0:
            return self.min_output # Avoid division by zero

        process_variable = observation.get('process_variable')
        if process_variable is None:
            # Handle cases where the observation is not as expected
            # Returning a neutral or safe value
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        error = self.setpoint - process_variable

        # Proportional term
        p_term = self.Kp * error

        # Integral term (with anti-windup logic handled during clamping)
        # Note: The integral term is updated *after* checking for saturation
        i_term = self.Ki * self._integral

        # Derivative term
        derivative = (error - self._previous_error) / dt
        d_term = self.Kd * derivative

        # Compute raw, unclamped output
        output = p_term + i_term + d_term

        # Clamp the output and apply anti-windup
        if output > self.max_output:
            clamped_output = self.max_output
            # Anti-windup: Do not increase integral if output is maxed out and error is positive
            if error > 0:
                pass # Don't integrate
            else:
                self._integral += error * dt
        elif output < self.min_output:
            clamped_output = self.min_output
            # Anti-windup: Do not decrease integral if output is minned out and error is negative
            if error < 0:
                pass # Don't integrate
            else:
                self._integral += error * dt
        else:
            clamped_output = output
            # Only integrate if the output is not saturated
            self._integral += error * dt

        # Update state for next iteration
        self._previous_error = error
        self._previous_output = clamped_output

        return clamped_output

    def set_setpoint(self, new_setpoint: float):
        """
        Updates the controller's setpoint and resets internal states.
        """
        if self.setpoint != new_setpoint:
            print(f"PIDController setpoint updated from {self.setpoint} to {new_setpoint}.")
            self.setpoint = new_setpoint
            # Reset integral and derivative error to prevent output jumps
            self._integral = 0
            self._previous_error = 0 # Or set to current error if smooth transition is needed
