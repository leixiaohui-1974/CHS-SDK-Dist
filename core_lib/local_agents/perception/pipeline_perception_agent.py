"""
Perception Agent for a pipeline, acting as its digital twin.
"""
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.physical_objects.pipe import Pipe
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class PipelinePerceptionAgent(DigitalTwinAgent):
    """
    A specialized Digital Twin Agent for monitoring a Pipe object.

    This agent wraps a Pipe simulation model, periodically fetching its state
    and publishing it to a designated topic on the message bus. While it currently
    relies on the base DigitalTwinAgent functionality, it is designed to be
    extensible for future features like leak detection or online parameter
    identification (e.g., friction factor).
    """

    def __init__(self,
                 agent_id: str,
                 pipe_model: Pipe,
                 message_bus: MessageBus,
                 state_topic: str):
        """
        Initializes the PipelinePerceptionAgent.

        Args:
            agent_id: The unique ID of this agent.
            pipe_model: The Pipe simulation model this agent is a twin of.
            message_bus: The system's message bus for communication.
            state_topic: The topic on which to publish the pipe's state.
        """
        super().__init__(agent_id=agent_id,
                         simulated_object=pipe_model,
                         message_bus=message_bus,
                         state_topic=state_topic)

        print(f"PipelinePerceptionAgent '{self.agent_id}' created for Pipe '{pipe_model.name}'.")
