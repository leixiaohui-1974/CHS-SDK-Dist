#!/usr/bin/env python3
"""
Example runner for Scenario 6: Fault Tolerance.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationLoader
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ConstantInflowAgent(Agent):
    """Provides a constant inflow."""
    def __init__(self, agent_id: str, message_bus: MessageBus, inflow_topic: str, inflow_rate: float):
        super().__init__(agent_id)
        self.bus, self.topic, self.rate = message_bus, inflow_topic, inflow_rate
    def run(self, current_time: float):
        self.bus.publish(self.topic, {'inflow_rate': self.rate})


class LocalGateControlAgent(Agent):
    """Controls a gate based on a dynamic setpoint and can be shut down."""
    def __init__(self, agent_id: str, message_bus: MessageBus, state_subscription_topic: str,
                 action_topic: str, initial_setpoint: float,
                 command_subscription_topic: Optional[str] = None, shutdown_topic: Optional[str] = None):
        super().__init__(agent_id)
        self.bus, self.action_topic = message_bus, action_topic
        self.setpoint = initial_setpoint
        self.is_active = True
        self.gate_is_open = False
        logging.info(f"[{self.agent_id}] Initialized with setpoint {self.setpoint:.2f}m")
        self.bus.subscribe(state_subscription_topic, self.handle_state_message)
        if command_subscription_topic:
            self.bus.subscribe(command_subscription_topic, self.handle_command_message)
        if shutdown_topic:
            self.bus.subscribe(shutdown_topic, self.handle_shutdown_message)

    def handle_state_message(self, message: Dict[str, Any]):
        if not self.is_active: return
        water_level = message.get('water_level')
        if water_level is None: return
        if water_level > self.setpoint and not self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m > setpoint {self.setpoint:.2f}m. Opening gate.")
            self.bus.publish(self.action_topic, {'opening': 1.0})
            self.gate_is_open = True
        elif water_level <= self.setpoint and self.gate_is_open:
            logging.info(f"[{self.agent_id}] Level {water_level:.2f}m <= setpoint {self.setpoint:.2f}m. Closing gate.")
            self.bus.publish(self.action_topic, {'opening': 0.0})
            self.gate_is_open = False

    def handle_command_message(self, message: Dict[str, Any]):
        if not self.is_active: return
        new_setpoint = message.get('setpoint')
        if new_setpoint is not None:
            logging.info(f"[{self.agent_id}] Received new setpoint command: {new_setpoint:.2f}m. Previous was {self.setpoint:.2f}m.")
            self.setpoint = new_setpoint

    def handle_shutdown_message(self, message: Dict[str, Any]):
        if message.get('shutdown') == True:
            logging.warning(f"[{self.agent_id}] Received SHUTDOWN command. Ceasing operations.")
            self.is_active = False

    def run(self, current_time: float): pass


class FailureInjectionAgent(Agent):
    """Issues a shutdown command at a specific time."""
    def __init__(self, agent_id: str, message_bus: MessageBus, target_topic: str, failure_time: float):
        super().__init__(agent_id)
        self.bus, self.topic, self.time = message_bus, target_topic, failure_time
        self.fault_injected = False
    def run(self, current_time: float):
        if not self.fault_injected and current_time >= self.time:
            logging.critical(f"[{self.agent_id}] Injecting failure at time {current_time:.2f}s on topic {self.topic}")
            self.bus.publish(self.topic, {'shutdown': True})
            self.fault_injected = True


class SupervisoryAgent(Agent):
    """Monitors two reservoirs and takes corrective action if they deviate."""
    def __init__(self, agent_id: str, message_bus: MessageBus, state_topic_A: str, state_topic_B: str,
                 command_topic_B: str, deviation_threshold: float, corrective_setpoint: float):
        super().__init__(agent_id)
        self.bus = message_bus
        self.command_topic_B = command_topic_B
        self.threshold = deviation_threshold
        self.corrective_setpoint = corrective_setpoint
        self.level_A, self.level_B = None, None
        self.corrective_action_taken = False
        self.bus.subscribe(state_topic_A, self.handle_state_A)
        self.bus.subscribe(state_topic_B, self.handle_state_B)

    def handle_state_A(self, msg): self.level_A = msg.get('water_level')
    def handle_state_B(self, msg): self.level_B = msg.get('water_level')

    def run(self, current_time: float):
        if self.corrective_action_taken or self.level_A is None or self.level_B is None:
            return
        deviation = abs(self.level_A - self.level_B)
        if deviation > self.threshold:
            logging.warning(f"[{self.agent_id}] Deviation ({deviation:.2f}m) exceeds threshold ({self.threshold:.2f}m). Taking corrective action.")
            command_message = {'setpoint': self.corrective_setpoint}
            self.bus.publish(self.command_topic_B, command_message)
            self.corrective_action_taken = True


def run_fault_tolerance_simulation():
    """Sets up and runs the fault tolerance simulation."""
    scenario_path = Path(__file__).parent
    logging.info("--- Setting up Example 6: Fault Tolerance ---")
    loader = SimulationLoader(scenario_path=str(scenario_path))
    harness = SimulationHarness(config=loader.config.get('simulation', {}))
    message_bus = harness.message_bus
    loader.harness = harness

    # Load components
    for comp_conf in loader.components_config.get('components', []):
        comp_id, CompClass = comp_conf['id'], loader._get_class(comp_conf['class'])
        params = {'name': comp_id, 'initial_state': comp_conf.get('initial_state', {}),
                  'parameters': comp_conf.get('parameters', {}), 'message_bus': message_bus}
        if comp_conf['class'] == 'Reservoir': params['inflow_topic'] = f"inflow/{comp_id}"
        elif comp_conf['class'] == 'Gate': params['action_topic'] = f"action/gate/{comp_id}"
        instance = CompClass(**params)
        harness.add_component(instance)
        loader.component_instances[comp_id] = instance

    loader._load_topology()

    # Load agents
    for agent_conf in loader.agents_config.get('agents', []):
        agent_id, cls, cfg = agent_conf['id'], agent_conf['class'], agent_conf.get('config', {})
        instance = None
        if cls == "DigitalTwinAgent":
            sim_obj = loader.component_instances[cfg['simulated_object_id']]
            instance = loader._get_class(cls)(agent_id=agent_id, message_bus=message_bus, simulated_object=sim_obj, state_topic=cfg['state_topic'])
        elif cls == "ConstantInflowAgent":
            instance = ConstantInflowAgent(agent_id=agent_id, message_bus=message_bus, inflow_topic=f"inflow/{cfg['target_component_id']}", inflow_rate=cfg['inflow_rate'])
        elif cls == "LocalGateControlAgent":
            instance = LocalGateControlAgent(agent_id=agent_id, message_bus=message_bus,
                                             state_subscription_topic=cfg['state_subscription_topic'],
                                             action_topic=cfg['action_topic'],
                                             initial_setpoint=cfg['initial_setpoint'],
                                             command_subscription_topic=cfg.get('command_subscription_topic'),
                                             shutdown_topic=cfg.get('shutdown_topic'))
        elif cls == "FailureInjectionAgent":
            instance = FailureInjectionAgent(agent_id=agent_id, message_bus=message_bus, target_topic=cfg['target_topic'], failure_time=cfg['failure_time'])
        elif cls == "SupervisoryAgent":
            instance = SupervisoryAgent(agent_id=agent_id, message_bus=message_bus,
                                        state_topic_A=cfg['state_topic_A'], state_topic_B=cfg['state_topic_B'],
                                        command_topic_B=cfg['command_topic_B'],
                                        deviation_threshold=cfg['deviation_threshold'],
                                        corrective_setpoint=cfg['corrective_setpoint'])
        if instance:
            harness.add_agent(instance)

    harness.build()
    logging.info("\n--- Running Simulation ---")
    harness.run_mas_simulation()
    logging.info("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_fault_tolerance_simulation()
