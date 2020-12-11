#!/usr/bin/env python

import os, json, logging, time, random

from broker.connection import connect

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None))

connection = connect()

channel = connection.channel()

for i in range(int(os.getenv("NUMBER_OF_MESSAGES", 10))):
    logging.debug(f"Initial message {i} published")
    channel.basic_publish(exchange='', routing_key="service_a", body=json.dumps(["seq-"+str(i)]))

logging.info("All initial messages published")
connection.close()