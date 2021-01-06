#!/usr/bin/env python

import os, time, logging, json
import pika
from pika.exceptions import AMQPConnectionError
from pymongo import MongoClient
from flatten_dict import flatten
from bson import ObjectId

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

class Broker:
    def __init__(self, host, port, user, password, connection_attempts=10, connection_attempt_delay=10, data_store=None):
        # the field to track the message chain id in both rabbit and redis
        self.id_field = "_id"
        self.consume_channel = None
        self.publish_channel = None

        # start a client for data storage
        if data_store is None:
            client = MongoClient(os.getenv("MONGODB_HOST", "localhost"))
            data_store = client.get_database(os.getenv("MONGODB_DB", "broker"))
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
            data = self.data_store.get_collection(os.getenv("MONGODB_COLLECTION", "messages")).find_one({self.id_field: ObjectId(body[self.id_field])})

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

        if self.id_field in data:
            # update data
            self.data_store.get_collection(os.getenv("MONGODB_COLLECTION", "messages")).update_one({self.id_field: ObjectId(data[self.id_field])}, {"$set": flatten(data, reducer="dot")})
        else:
            # insert and fetch id
            result = self.data_store.get_collection(os.getenv("MONGODB_COLLECTION", "messages")).insert_one(data)
            message[self.id_field] = result.inserted_id

        # convert BSON object id to a string
        if isinstance(message[self.id_field], ObjectId):
            message[self.id_field] = str(message[self.id_field])

        self.publish_channel.basic_publish(exchange='', routing_key=key, body=json.dumps(message))
