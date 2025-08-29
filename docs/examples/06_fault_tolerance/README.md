# Example 6: Fault Tolerance and System Adaptation

This example demonstrates a more advanced distributed system capability: detecting a component failure and adapting the system's behavior to mitigate the impact.

## Scenario

We have a system with two parallel reservoirs, `reservoir_A` and `reservoir_B`. Each has its own inflow and a downstream gate, `gate_A` and `gate_B`.

The control system is structured in three layers:
1.  **Local Control**: Two `LocalGateControlAgent` instances (`controller_A` and `controller_B`) are responsible for maintaining a water level setpoint of 51.0m in their respective reservoirs by opening and closing their gates.
2.  **Failure Injection**: A special `FailureInjectionAgent` is introduced to simulate a fault. At `t=150` seconds, it will "kill" `controller_A` by sending it a "shutdown" command, preventing it from controlling `gate_A`.
3.  **Supervisory Control**: A `SupervisoryAgent` monitors the water levels of both reservoirs. If it detects that one reservoir's level is deviating significantly from the other (by more than 1.0m), it assumes a failure has occurred. It then takes corrective action by commanding the *healthy* controller (`controller_B`) to switch to a more aggressive control strategy (a lower setpoint of 50.2m) to increase its outflow and compensate for the failure.

This demonstrates a fault-tolerant system that can:
-   Detect anomalies (a component failure leading to state deviation).
-   Adapt its strategy to continue pursuing the overall system goal (managing water levels).

## How to Run

To run this simulation, execute the `run.py` script in this directory:

```bash
python run.py
```
You will observe both systems operating normally. At t=150s, controller_A will fail. Shortly after, the water level in reservoir_A will rise, triggering the supervisory agent to command controller_B to a new, lower setpoint.
