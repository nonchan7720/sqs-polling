from typing import Any

from sqs_polling import heartbeat, polling, ready
from sqs_polling.handler import Polling
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
def simple(
    self: Polling,
    message_body: str,
    message_attribute: dict[str, Any] | None,
    message_group_id: str | None,
    message_duplication_id: str | None,
):
    import json
    from pprint import pprint

    data: dict[str, Any] = json.loads(message_body)
    data.update(message_attribute or {})
    pprint(data)


@ready.connect
def ready_():
    logger.info("Ready.")


@heartbeat.connect
def heartbeat_():
    logger.info("HeartBeat.")
