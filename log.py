#!/usr/bin/env python

import os, logging

from broker.connection import connect

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None))

def main():
    queue_name = os.getenv("RABBITMQ_QUEUE", "")

    connection = connect()

    inbox = connection.channel()
    inbox.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        logging.debug(f"Received message on logger: {body}")

        logging.info(body)

        logging.debug(f"Acking message on logger")
        ch.basic_ack(method.delivery_tag)

    inbox.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

    logging.debug("Waiting for messages")
    inbox.start_consuming()

if __name__ == "__main__":
    main()