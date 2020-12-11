#!/usr/bin/env python
import os, pika, time, logging
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

def connect():
    connection_attempts = int(os.getenv("RABBITMQ_ATTEMPTS", 10))
    credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASS", "guest"))
    conn_parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=os.getenv("RABBITMQ_PORT", 5672),
        credentials=credentials,
        virtual_host='/'
    )

    for _ in range(connection_attempts):
        try:
            return pika.BlockingConnection(conn_parameters)
        except AMQPConnectionError:
            logger.debug("Waiting for Message Broker")
            time.sleep(int(os.getenv("RABBITMQ_CONNECTION_DELAY", 10)))
            pass
