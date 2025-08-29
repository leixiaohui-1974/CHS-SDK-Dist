import pika
import json
import sys

def main():
    """Connects to RabbitMQ and consumes messages from the water system exchange."""
    try:
        # Connect to RabbitMQ server on localhost
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declare the same topic exchange as the producer
        exchange_name = 'water_system_exchange'
        channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)

        # Declare an exclusive queue. When the consumer disconnects, the queue is deleted.
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        # Bind the queue to the exchange to receive all messages.
        # The '#' binding key means "receive all messages regardless of routing key".
        binding_key = '#'
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_key)

        print(' [*] Waiting for messages. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            """Callback function to process received messages."""
            try:
                payload = json.loads(body)
                print(f" [x] Received on topic '{method.routing_key}':")
                print(json.dumps(payload, indent=2))
            except json.JSONDecodeError:
                print(f" [!] Received non-JSON message on topic '{method.routing_key}': {body.decode()}")


        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error: Could not connect to RabbitMQ at localhost. Is it running?")
        print(f"Details: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            pass

if __name__ == '__main__':
    main()
