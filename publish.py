#!/usr/bin/env python

import os, logging, time
from broker.broker import Broker

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), None))

broker = Broker(
    os.getenv("RABBITMQ_HOST", "localhost"),
    os.getenv("RABBITMQ_PORT", 5672),
    os.getenv("RABBITMQ_USER", "guest"),
    os.getenv("RABBITMQ_PASS", "guest")
)

# generate a few messages
for i in range(int(os.getenv("NUMBER_OF_MESSAGES", 10))):
    logging.debug(f"Initial message {i} published")
    broker.publish("service_a", {"history": ["seq-"+str(i)]}, {"created_at": time.time()})

logging.info("All initial messages published")