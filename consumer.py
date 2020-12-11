#!/usr/bin/env python

import os, json, logging, time, random

from broker.connection import connect

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None))

def main():
    queue_name = os.getenv("RABBITMQ_QUEUE", "")

    connection = connect()

    inbox = connection.channel()
    inbox.queue_declare(queue=queue_name)

    general = connection.channel()
    general.queue_declare(queue='')


    def callback(ch, method, properties, body):
        logging.debug(f"Received message on {queue_name}: {body}")

        body_arr = json.loads(body)

        body_arr.append(queue_name)
        new_body = json.dumps(body_arr)
        new_key = os.getenv("RABBITMQ_NEXT_QUEUE", "")

        # take some time to do a task
        time.sleep(random.randint(int(os.getenv("RANDOM_WAIT_MIN", 5)), int(os.getenv("RANDOM_WAIT_MAX", 10))))

        logging.debug(f"Publishing message on {new_key}: {new_body}")
        general.basic_publish(exchange='', routing_key=new_key, body=new_body)

        logging.debug(f"Acking message on {queue_name}")
        ch.basic_ack(method.delivery_tag)

    inbox.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

    logging.debug(f"Waiting for messages {queue_name}")
    inbox.start_consuming()

if __name__ == "__main__":
    main()