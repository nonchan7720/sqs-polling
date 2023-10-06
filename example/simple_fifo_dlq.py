from sqs_polling import heartbeat, polling, ready
from sqs_polling.exceptions import RejectDLQException
from sqs_polling.handler import Polling
from sqs_polling.polling import logger


@polling(
    queue_name="test-sns-to-sqs.fifo",
    aws_profile={
        "region_name": "ap-northeast-1",
        "aws_access_key_id": "dummy",
        "aws_secret_access_key": "dummy",
        "endpoint_url": "http://localstack:4566",
    },
)
def simple(self: Polling, *args, **kwargs):
    from pprint import pprint

    logger.info("simple received.")
    kwargs.update({"retry": self.retry})
    pprint(kwargs)
    raise RejectDLQException()


@ready.connect
def ready_():
    logger.info("Ready.")


@heartbeat.connect
def heartbeat_():
    logger.info("HeartBeat.")
