#!/usr/bin/env python

import os, logging, time

from broker.broker import Broker

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None))

def main():
    broker = Broker(
        os.getenv("RABBITMQ_HOST", "localhost"),
        os.getenv("RABBITMQ_PORT", 5672),
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASS", "guest")
    )

    queue_name = os.getenv("RABBITMQ_QUEUE", "")

    def callback(ch, method, properties, body, data):
        logging.debug(f"Received message on logger: {body}\n\n{data}")

        data['completed_at'] = time.time()
        data['transfer_duration'] = data['completed_at'] - data['created_at'] - data['delay']

        # log the result of each message chain
        logging.info(body)
        logging.info(data)

        # ack the message
        return True

    logging.debug("Waiting for messages")
    broker.consume(queue_name, callback)

if __name__ == "__main__":
    main()