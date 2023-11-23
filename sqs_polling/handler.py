import json
from typing import Any, Callable, TypeVar

from sqs_polling.types import RedrivePolicy


def __default_decode(x: str) -> str:
    return x


TMessageBody = TypeVar("TMessageBody")
TMessageAttribute = dict[str, Any] | None
TMessageGroupId = str | None
TMessageDeduplicationId = str | None

THandle = Callable[
    [
        "Polling",
        TMessageBody,
        TMessageAttribute,
        TMessageGroupId,
        TMessageDeduplicationId,
    ],
    None,
]

TDecode = Callable[[str], TMessageBody] | None


class Polling:
    def __init__(
        self,
        *,
        queue_name: str = "",
        queue_url: str = "",
        visibility_timeout: int = 10,
        handler: THandle = lambda self, message_body, message_attribute, message_group_id, message_duplication_id: None,
        exception_deletable: bool = False,
        interval_seconds: float = 1.0,
        max_workers: int = 1,
        max_number_of_messages: int = 1,
        process_worker: bool = False,
        aws_profile: dict[str, Any] = {},
        max_retry_count: int = 0,
        decoder: TDecode[TMessageBody] = None
    ) -> None:
        if queue_name == "" and queue_url == "":
            raise ValueError("Either queue_name or queue_url must be specified.")
        self.queue_name = queue_name
        self.__queue_url = queue_url
        self.handler: THandle = handler
        self.visibility_timeout = visibility_timeout
        self.exception_deletable = exception_deletable
        self.interval_seconds = interval_seconds
        self.max_workers = max_workers
        self.max_number_of_messages = max_number_of_messages
        self.process_worker = process_worker
        self.aws_profile = aws_profile
        self.__retry = 0
        self.__max_retry_count = max_retry_count
        self.__dead_later_queue_url = ""
        self.decorator = decoder or __default_decode

    @property
    def retry(self) -> int:
        return self.__retry

    @retry.setter
    def retry(self, value: int):
        self.__retry = value

    @property
    def queue_url(self) -> str:
        return self.__queue_url

    @property
    def dead_later_queue_url(self) -> str:
        return self.__dead_later_queue_url

    def set_queue_url(self, client) -> None:
        if self.__queue_url == "":
            self.__queue_url = self.__get_queue_url(client, self.queue_name)

    def update(self, **kwargs) -> None:
        self.__queue_url = kwargs.get("queue_url", self.__queue_url)
        self.visibility_timeout = kwargs.get(
            "visibility_timeout", self.visibility_timeout
        )
        self.exception_deletable = kwargs.get(
            "exception_deletable", self.exception_deletable
        )
        self.interval_seconds = kwargs.get("interval_seconds", self.interval_seconds)
        self.max_workers = kwargs.get("max_workers", self.max_workers)
        self.max_number_of_messages = kwargs.get(
            "max_number_of_messages", self.max_number_of_messages
        )
        self.process_worker = kwargs.get("process_worker", self.process_worker)
        self.aws_profile = kwargs.get("aws_profile", self.aws_profile)
        self.decorator = kwargs.get("decorator", self.decorator)

    def connect(self, func: THandle) -> None:
        self.handler = func

    def is_max_retry(self) -> bool:
        return self.__max_retry_count > 0 and self.retry >= self.__max_retry_count

    def set_dead_later_queue_url(self, client) -> None:
        attr = client.get_queue_attributes(
            QueueUrl=self.queue_url, AttributeNames=["RedrivePolicy"]
        )
        value = attr.get("Attributes", {}).get("RedrivePolicy")
        if value:
            policy: RedrivePolicy = json.loads(value)
            queue_arn = policy.get("deadLetterTargetArn", "")
            dead_later_queue_name = queue_arn.split(":")[-1]
            self.__dead_later_queue_url = self.__get_queue_url(
                client, dead_later_queue_name
            )

    def __get_queue_url(self, client, queue_name) -> str:
        resp = client.get_queue_url(QueueName=queue_name)
        return resp.get("QueueUrl")


_handlers: dict[str, Polling] = {}


def set_handler(name: str, p: Polling) -> None:
    _handlers[name] = p


def get_handler(name: str) -> Polling:
    return _handlers[name]
