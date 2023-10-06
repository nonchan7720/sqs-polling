from sqs_polling import heartbeat, polling, ready
from sqs_polling.exceptions import RetryException
from sqs_polling.handler import Polling
from sqs_polling.polling import logger


@polling(
    queue_url="http://localstack:4566/000000000000/test-sns-to-sqs",
    max_number_of_messages=5,
    aws_profile={
        "region_name": "ap-northeast-1",
        "aws_access_key_id": "dummy",
        "aws_secret_access_key": "dummy",
        "endpoint_url": "http://localstack:4566",
    },
    max_retry_count=2,
)
def execute_error(self: Polling, *args, **kwargs):
    import random
    from pprint import pprint

    logger.info("execute_error received.")
    random_ = random.SystemRandom()

    a = random_.randint(1, 10)

    if a % 2 == 0:
        raise RetryException()
    else:
        kwargs.update({"retry": self.retry})
        pprint(kwargs)


@ready.connect
def ready_():
    logger.info("Ready.")


@heartbeat.connect
def heartbeat_():
    logger.info("HeartBeat.")
