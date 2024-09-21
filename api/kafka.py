from confluent_kafka import Producer, Consumer


def create_producer():
    producer = Producer({"bootstrap.servers": "localhost:9092"})
    return producer


def create_consumer(group_id):
    consumer = Consumer(
        {
            "bootstrap.servers": "localhost:9092",
            "group.id": group_id,
            "auto.offset.reset": "earliest",
        }
    )
    return consumer
