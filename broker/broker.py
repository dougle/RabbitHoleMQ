#!/usr/bin/env python
import os, time, logging, json, uuid
import pika, redis
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

class Broker:
    def __init__(self, host, port, user, password, connection_attempts=10, connection_attempt_delay=10, data_store=None):
        # the field to track the message chain id in both rabbit and redis
        self.id_field = "broker_message_id"
        self.consume_channel = None
        self.publish_channel = None

        # start a client for data storage
        if data_store is None:
            data_store = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=os.getenv("REDIS_PORT", 6379),
                db=os.getenv("REDIS_DB", 0)
            )
        self.data_store = data_store

        conn_parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(user, password),
            virtual_host='/'
        )

        # keep trying to connect while message service starts
        for _ in range(int(connection_attempts)):
            try:
                self.connection = pika.BlockingConnection(conn_parameters)
            except AMQPConnectionError:
                logger.debug("Waiting for Message Broker")
                time.sleep(int(connection_attempt_delay))
                pass

    def __del__(self):
        self.connection.close()

    def consume(self, queue, callback):
        # consumer callback wrapper
        def fetch_data(ch, method, properties, body_json):
            body = json.loads(body_json)
            data = json.loads(self.data_store.get(body.get(self.id_field)))

            # if the callback returns true ack the message
            if callback(ch, method, properties, body, data or {}):
                ch.basic_ack(delivery_tag=method.delivery_tag)

        if self.consume_channel is None:
            self.consume_channel = self.connection.channel()

        self.consume_channel.queue_declare(queue=queue)

        self.consume_channel.basic_consume(queue=queue, on_message_callback=fetch_data, auto_ack=False)
        self.consume_channel.start_consuming()

    def publish(self, key, message, data={}):
        if not isinstance(message, dict):
            raise Exception(f"Publish message is not a dict")

        if not isinstance(data, dict):
            raise Exception(f"Publish data is not a dict")

        if self.publish_channel is None:
            self.publish_channel = self.connection.channel()

        # get or generate a message identifier
        message[self.id_field] = message.get(self.id_field, str(uuid.uuid4()))

        self.data_store.set(message[self.id_field], json.dumps(data), os.getenv("REDIS_TTL", 600))
        self.publish_channel.basic_publish(exchange='', routing_key=key, body=json.dumps(message))
