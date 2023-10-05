from sqs_polling import heartbeat, polling, ready
from sqs_polling.polling import logger


@polling(
    "http://localstack:4566/000000000000/test-sns-to-sqs",
    60,
    aws_profile={
        "region_name": "ap-northeast-1",
        "aws_access_key_id": "dummy",
        "aws_secret_access_key": "dummy",
        "endpoint_url": "http://localstack:4566",
    },
)
def simple(*args, **kwargs):
    import time
    from pprint import pprint

    logger.info("simple received.")
    time.sleep(2)
    pprint(kwargs)


@ready.connect
def ready_():
    logger.info("Ready.")


@heartbeat.connect
def heartbeat_():
    logger.info("HeartBeat.")
