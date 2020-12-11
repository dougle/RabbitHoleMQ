# RabbitHoleMQ
A quick play around using RabbitMQ as a message broker, router, and queue between simple services

The queue messages originate in the container `first`, these messages are a json array with the only element set to the message number `["seq-1"]`

Each service has ten workers picking messages off of the relevant queue, services simply add their queue name to the json array in the message body.

### Usage
Run `docker-compose up`

First pip will install a rabbitmq module, rabbitmq will flood the logs with messages and then eventually you should see some messages reaching the final logging service.

```plain
last_1            | INFO:root:b'["seq-97", "service_a", "service_b", "service_c"]'
last_1            | INFO:root:b'["seq-98", "service_a", "service_b", "service_c"]'
last_1            | INFO:root:b'["seq-91", "service_a", "service_b", "service_c"]'
last_1            | INFO:root:b'["seq-86", "service_a", "service_b", "service_c"]'
last_1            | INFO:root:b'["seq-88", "service_a", "service_b", "service_c"]'
```
Notice that the services worked on these messages in order (a,b,c), but the sequence of messages completed as soon as they could (seq-98 completed before seq-88).

RabbitMQ has a default exchange (blank queue name) which will bind to all queues, the key is used to select which queue the message appears in. This is useful to serve as a single message input while RabbitMQ does the routing for us.

The flow is as follows:
* `publish.py` in container `first` will generate a load of messages and send them to RabbitMQ's default exchange.
* `consumer.py` in the scaled service containers picks up messages (depending on `routing_key`) and does some trivial task with them
* Each service republishes the new message to the next service.
* `log.py` in the container `last` picks up the completed message and logs it out.