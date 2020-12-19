# RabbitHoleMQ
A quick play around using RabbitMQ as a message broker, router, and queue between simple services, in much the same way [CAN Bus](https://en.wikipedia.org/wiki/CAN_bus) does.

This could progress and be implemented to replace HTTP based APIs between microservices to add a message buffer and message preservation during times of increased load. It could also increase asynchronicity between microservices because HTTP connections wouldn't be idle waiting for a response.

The queue messages originate in the container `first`, these messages are a json array with the only element set to the message number `["seq-1"]`

Each service has ten workers picking messages off of the relevant queue, services simply add their queue name to the json array in the message body and add a timestamp to the data object.

### Usage
Run `docker-compose up`

First pip will install a rabbitmq module, rabbitmq will flood the logs with messages and then eventually you should see some messages and data reaching the final logging service.

```plain
last_1            | INFO:root:{'history': ['seq-94', 'service_a', 'service_b', 'service_c'], 'broker_message_id': '6dbcf262-f3b4-4a76-9063-af5d03313b11'}
last_1            | INFO:root:{'created_at': 1608404747.2754867, 'updated_at': 1608404852.3569171, 'service_a': 1608404839.339323, 'service_b': 1608404846.3474588, 'service_c': 1608404852.3569193, 'completed_at': 1608404861.3698623}

last_1            | INFO:root:{'history': ['seq-89', 'service_a', 'service_b', 'service_c'], 'broker_message_id': '58c7793f-0fdb-4175-a0a9-7c0f25eea39f'}
last_1            | INFO:root:{'created_at': 1608404747.2737725, 'updated_at': 1608404855.335938, 'service_a': 1608404838.3148792, 'service_b': 1608404845.3241074, 'service_c': 1608404855.3359404, 'completed_at': 1608404863.3479698}

last_1            | INFO:root:{'history': ['seq-99', 'service_a', 'service_b', 'service_c'], 'broker_message_id': '1df7b375-4eec-47f4-8458-6d98bde674e1'}
last_1            | INFO:root:{'created_at': 1608404747.277131, 'updated_at': 1608404856.3556948, 'service_a': 1608404841.3345957, 'service_b': 1608404847.343761, 'service_c': 1608404856.3556972, 'completed_at': 1608404863.3671978}
```

Notice that the services worked on these messages in order (a,b,c), but the sequence of messages completed as soon as they could (seq-94 completed before seq-89).

RabbitMQ has a default exchange (blank queue name) which will bind to all queues, the key is used to select which queue the message appears in. This is useful to serve as a single message input while RabbitMQ does the routing for us.

The flow is as follows:
* `publish.py` in container `first` will generate a load of messages and send them to RabbitMQ's default exchange.
* `consumer.py` in the scaled service containers picks up messages (depending on `routing_key`) and does some trivial task with them
* Each service republishes the new message to the next service.
* `log.py` in the container `last` picks up the completed message and logs it out.