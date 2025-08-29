"""
This module contains predefined rule sets for the rule-based CentralDispatcher.
A rule set is a dictionary of profiles, where each profile has a condition
(a lambda function) and a set of commands to execute if the condition is met.
"""

# Rule set for the Joint Watershed Dispatch example (Mission 2.3)
# This defines the high-level operational logic for flood management.
joint_dispatch_rules = {
    "profiles": {
        "flood": {
            # Condition: The reservoir's water level has exceeded the flood warning threshold.
            "condition": lambda states: states.get('reservoir', {}).get('water_level', 0) > 22.0,
            # Commands: Issue a high outflow target to the hydro station and close the downstream diversion.
            "commands": {
                "hydro_station_control": {"new_setpoint": 400},
                "diversion_gate_control": {"new_setpoint": 0.0}
            }
        },
        "normal": {
            # Condition: Default profile if no other conditions are met.
            "condition": lambda states: True,
            # Commands: Maintain normal operational targets.
            "commands": {
                "hydro_station_control": {"new_setpoint": 100},
                "diversion_gate_control": {"new_setpoint": 1.0}
            }
        }
    }
}

# A dictionary to map rule set names (used in JSON configs) to the actual rule set objects.
RULE_SETS = {
    "joint_dispatch_rules": joint_dispatch_rules
}
