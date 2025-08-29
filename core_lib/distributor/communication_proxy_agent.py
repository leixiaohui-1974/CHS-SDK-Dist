import json
import logging
import queue
import threading
import time
from typing import List

import pika
from pika.exceptions import AMQPError

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

logger = logging.getLogger(__name__)

class CommunicationProxyAgent(Agent):
    """
    Acts as a thread-safe bridge between the internal MessageBus and RabbitMQ.

    This agent uses a dedicated background thread for all RabbitMQ communications
    to ensure thread-safety with the Pika library. It uses a thread-safe
    Python queue to pass messages from the main simulation thread to the
    RabbitMQ thread.
    """

    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 amqp_url: str,
                 exchange_name: str = 'water_system_exchange',
                 topics_to_forward: List[str] = None,
                 inbound_queue_name: str = 'inbound_to_simulation'):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.amqp_url = amqp_url
        self.exchange_name = exchange_name
        self.topics_to_forward = topics_to_forward or []
        self.inbound_queue_name = inbound_queue_name

        self._outgoing_queue = queue.Queue()
        self.is_running = True
        self._rabbitmq_thread = threading.Thread(target=self._run_rabbitmq_loop, daemon=True)
        self._rabbitmq_thread.start()

        self._setup_local_subscriptions()
        logger.info(f"CommunicationProxyAgent '{self.agent_id}' initialized.")

    def _setup_local_subscriptions(self):
        """Subscribes to local topics to put messages onto the outgoing queue."""
        for topic in self.topics_to_forward:
            self.message_bus.subscribe(topic, lambda msg, t=topic: self._forward_to_external(t, msg))
            logger.info(f"Agent '{self.agent_id}' subscribed to local topic: {topic}")

    def _forward_to_external(self, topic: str, message: Message):
        """
        Thread-safe method called by the main simulation thread.
        Places a message on the queue to be sent by the RabbitMQ thread.
        """
        self._outgoing_queue.put((topic, message))

    def _inject_into_local_bus(self, ch, method, properties, body):
        """Callback for received RabbitMQ messages. Injects them into the local bus."""
        try:
            topic = method.routing_key
            message = json.loads(body)
            logger.info(f"Agent '{self.agent_id}': Received message from RabbitMQ on topic '{topic}'.")
            self.message_bus.publish(topic, message)
        except json.JSONDecodeError:
            logger.error(f"Agent '{self.agent_id}': Could not decode incoming JSON message: {body}")
        except Exception as e:
            logger.error(f"Agent '{self.agent_id}': Failed to inject message into local bus: {e}")

    def _run_rabbitmq_loop(self):
        """The single, dedicated thread for all RabbitMQ interactions."""
        connection = None
        while self.is_running:
            try:
                if not connection or connection.is_closed:
                    logger.info(f"Agent '{self.agent_id}': Connecting to RabbitMQ at {self.amqp_url}...")
                    connection = pika.BlockingConnection(pika.URLParameters(self.amqp_url))

                channel = connection.channel()
                channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic', durable=True)
                channel.queue_declare(queue=self.inbound_queue_name, durable=True)
                channel.queue_bind(exchange=self.exchange_name, queue=self.inbound_queue_name, routing_key='command.*')
                channel.basic_consume(queue=self.inbound_queue_name, on_message_callback=self._inject_into_local_bus, auto_ack=True)

                logger.info(f"Agent '{self.agent_id}': RabbitMQ connection established.")

                while self.is_running and channel.is_open:
                    # Process incoming messages without blocking indefinitely
                    channel.connection.process_data_events(time_limit=0.1)

                    # Process outgoing messages from the queue
                    try:
                        while not self._outgoing_queue.empty():
                            topic, message = self._outgoing_queue.get_nowait()
                            body = json.dumps(message, default=str)
                            channel.basic_publish(
                                exchange=self.exchange_name,
                                routing_key=topic,
                                body=body,
                                properties=pika.BasicProperties(content_type='application/json', delivery_mode=2)
                            )
                            self._outgoing_queue.task_done()
                    except queue.Empty:
                        continue # Normal condition, just means no outgoing messages

            except AMQPError as e:
                logger.error(f"Agent '{self.agent_id}': RabbitMQ error: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Agent '{self.agent_id}': Unexpected error in RabbitMQ loop: {e}")
                self.is_running = False

        if connection and connection.is_open:
            connection.close()
        logger.info(f"Agent '{self.agent_id}': RabbitMQ thread has shut down.")

    def run(self, current_time: float):
        """Called by the simulation harness. Checks if the background thread is alive."""
        if not self._rabbitmq_thread.is_alive():
            logger.critical(f"Agent '{self.agent_id}': RabbitMQ thread has died unexpectedly!")

    def stop(self):
        """Gracefully stops the agent and its background thread."""
        logger.info(f"Agent '{self.agent_id}': Stopping...")
        self.is_running = False
        self._rabbitmq_thread.join(timeout=2)
        logger.info(f"Agent '{self.agent_id}' has been stopped.")

    def __del__(self):
        """Ensure stop is called on garbage collection."""
        if self.is_running:
            self.stop()
