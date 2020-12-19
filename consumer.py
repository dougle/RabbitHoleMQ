#!/usr/bin/env python

import os, logging, time, random
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
    next_queue_name = os.getenv("RABBITMQ_NEXT_QUEUE", "")

    def callback(ch, method, properties, body, data={}):
        logging.debug(f"Received message on {queue_name}: {body} \n\n{data}")

        # add some tribial data to the message body and the data store
        body["history"].append(queue_name)
        data['updated_at'] = time.time()
        data[queue_name] = time.time()

        # take some time to do a task
        time.sleep(random.randint(int(os.getenv("RANDOM_WAIT_MIN", 5)), int(os.getenv("RANDOM_WAIT_MAX", 10))))

        # push the message on to the next service
        logging.debug(f"Publishing message on {next_queue_name}: {body}")
        broker.publish(next_queue_name, body, data)

        # True to ack the message
        return True

    logging.debug(f"Waiting for messages {queue_name}")
    broker.consume(queue_name, callback)

if __name__ == "__main__":
    main()