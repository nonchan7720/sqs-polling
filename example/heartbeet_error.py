from sqs_polling import heartbeat, polling, ready
from sqs_polling.polling import logger


@polling(
    queue_name="test-sns-to-sqs",
    aws_profile={
        "region_name": "ap-northeast-1",
        "aws_access_key_id": "dummy",
        "aws_secret_access_key": "dummy",
        "endpoint_url": "http://localstack:4566",
    },
)
def simple(self, *args, **kwargs):
    import time
    from pprint import pprint

    logger.info("simple received.")
    time.sleep(2)
    pprint(kwargs)


@ready.connect
def ready_():
    logger.info("Ready.")


counter = 0


@heartbeat.connect
def heartbeat_():
    import random

    global counter

    random_ = random.SystemRandom()

    a = random_.randint(1, 10)

    if a % 2 == 0:
        if counter >= 2:
            raise Exception("Heartbeat Test")
        counter += 1
    logger.info("HeartBeat.")
