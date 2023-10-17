from __future__ import annotations

import signal
import traceback
from asyncio import Event, all_tasks, create_task, current_task, gather, get_event_loop
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import wraps
from itertools import groupby
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable

import boto3

from .exceptions import RejectDLQException, RejectException, RetryException
from .execute_result import ExecuteResult
from .handler import Polling, THandle, set_handler
from .signal import handler_result, missing_receipt_handle
from .signal import shutdown as shutdown_signal

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from mypy_boto3_sqs import SQSClient
    from mypy_boto3_sqs.type_defs import MessageAttributeValueTypeDef, MessageTypeDef

ev = Event()
logger = getLogger(__name__)


async def shutdown(
    loop, executor: ProcessPoolExecutor | ThreadPoolExecutor, signal=None
) -> None:
    ev.set()
    if signal:
        logger.info(f"received exit signal {signal.name}...")
    shutdown_signal.send()
    executor.shutdown(wait=True, cancel_futures=False)
    tasks = [t for t in all_tasks() if t is not current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"cancelling {len(tasks)} outstanding tasks")

    await gather(*tasks, return_exceptions=True)
    logger.info("cancelled tasks")

    loop.stop()
    logger.info("gracefully shutdown the service.")


def polling(
    *,
    queue_name: str = "",
    queue_url: str = "",
    visibility_timeout: int = 10,
    exception_deletable: bool = False,
    interval_seconds: float = 1.0,
    max_workers: int = 1,
    max_number_of_messages: int = 1,
    process_worker: bool = False,
    aws_profile: dict[str, Any] = {},
    max_retry_count=0,
) -> Callable[[THandle], None]:
    def inner(func: THandle):
        @wraps(func)
        def _inner():
            p = Polling(
                queue_name=queue_name,
                queue_url=queue_url,
                visibility_timeout=visibility_timeout,
                handler=func,
                exception_deletable=exception_deletable,
                interval_seconds=interval_seconds,
                max_workers=max_workers,
                max_number_of_messages=max_number_of_messages,
                process_worker=process_worker,
                aws_profile=aws_profile,
                max_retry_count=max_retry_count,
            )
            set_handler(func.__name__, p)

        return _inner()

    return inner


_session: SQSClient | None = None


def _get_session(aws_profile_dict: dict[str, Any]) -> SQSClient:
    global _session

    if _session is None:
        _session = boto3.client("sqs", **aws_profile_dict)

    return _session


def _handler(
    p: Polling,
):
    sqs = _get_session(p.aws_profile)
    p.set_queue_url(sqs)
    p.set_dead_later_queue_url(sqs)

    Executor = ProcessPoolExecutor if p.process_worker else ThreadPoolExecutor
    with Executor(max_workers=p.max_workers + 1) as executor:
        loop = get_event_loop()
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                s,
                lambda s=s: create_task(
                    shutdown(loop=loop, executor=executor, signal=s)
                ),
            )
        loop.run_in_executor(
            executor,
            _polling,
            loop,
            executor,
            p,
        )
        loop.run_forever()
        loop.close()


def _polling(
    loop: AbstractEventLoop,
    executor: ThreadPoolExecutor | ProcessPoolExecutor,
    p: Polling,
):
    def _submit(message: MessageTypeDef):
        f = executor.submit(
            _execute,
            p,
            message,
            p.exception_deletable,
            p.aws_profile,
        )
        return f

    sqs = _get_session(p.aws_profile)

    messages = _sqs_receive(
        sqs, p.queue_url, p.visibility_timeout, p.max_number_of_messages
    )
    if len(messages) > 0:
        if p.queue_url.endswith(".fifo"):
            grouped_messages = groupby(
                messages, key=lambda x: x.get("Attributes", {}).get("MessageGroupId")
            )
            # メッセージグループ単位で順番に処理させる(非同期ではなく待機させる)
            for group_id, group_messages in grouped_messages:
                logger.info("Fifo queue", extra={"GroupId": group_id})
                messages = list(group_messages)
                for message in messages:
                    f = _submit(message)
                    f.result()
        else:
            [_submit(message) for message in messages]

    # shutdownを受け取った場合は新規ポーリングはしない
    if not ev.is_set():
        loop.call_later(
            p.interval_seconds,
            _polling,
            loop,
            executor,
            p,
        )


def _sqs_receive(
    sqs: SQSClient,
    queue_url: str,
    visibility_timeout: int,
    max_number_of_messages=1,
    wait_time_second=20,
):
    logger.info("Receiving.")
    response = sqs.receive_message(
        QueueUrl=queue_url,
        VisibilityTimeout=visibility_timeout,
        MaxNumberOfMessages=max_number_of_messages,
        WaitTimeSeconds=wait_time_second,
        AttributeNames=["All"],
        MessageAttributeNames=["All"],
    )
    if "Messages" in response:
        messages = [m for m in response["Messages"]]
        logger.info("Received messages.", extra={"length": len(messages)})
    else:
        logger.info("Empty messages.")
        messages = []

    return messages


def _execute(
    p: Polling,
    message: MessageTypeDef,
    exception_deletable: bool,
    aws_profile_dict: dict[str, Any],
):
    attribute = message.get("Attributes", {})
    retry_count = int(attribute.get("ApproximateReceiveCount", 1))
    p.retry = retry_count - 1  # 最初の受信分をマイナスする
    if p.is_max_retry():
        # 最大リトライ回数を超えた場合は再処理せずメッセージを削除する
        __finish_message(p, ExecuteResult.Reject, message, aws_profile_dict)
        return
    body = message.get("Body", "")
    result_type: ExecuteResult = ExecuteResult.Nil
    handler_result_kwargs = {
        "result_type": result_type,
        "retry_count": p.retry,
        "error_message": "",
        "stack_trace": "",
    }
    try:
        message_attribute: dict[str, Any] | None = None
        if _message_attribute := message.get("MessageAttributes"):
            message_attribute = {
                key: _get_message_attribute_value(value)
                for key, value in _message_attribute.items()
            }
        p.handler(
            p,
            body,
            message_attribute,
            attribute.get("MessageGroupId", None),
            attribute.get("MessageDeduplicationId", None),
        )
        result_type = ExecuteResult.Deletable
    except RetryException:
        result_type = ExecuteResult.Retry
    except RejectException:
        result_type = ExecuteResult.Reject
    except RejectDLQException:
        result_type = ExecuteResult.SendDLQ
    except Exception as e:
        handler_result_kwargs["error_message"] = str(e)
        handler_result_kwargs["stack_trace"] = traceback.format_exc()
        logger.error(e, exc_info=True, stack_info=True)
        result_type = (
            ExecuteResult.Deletable if exception_deletable else ExecuteResult.Retry
        )
    finally:
        handler_result_kwargs["result_type"] = result_type
        logger.debug("handler finally", extra={"result_type": str(result_type)})
        handler_result.send(**handler_result_kwargs)
        __finish_message(p, result_type, message, aws_profile_dict)


def __finish_message(
    p: Polling,
    result: ExecuteResult,
    message: MessageTypeDef,
    aws_profile_dict: dict[str, Any] = {},
):
    if handle := message.get("ReceiptHandle"):
        sqs = _get_session(aws_profile_dict)
        match result:
            case ExecuteResult.Deletable | ExecuteResult.Reject:
                logger.debug(
                    "Delete message", extra={"queue": p.queue_url, "handle": handle}
                )
                sqs.delete_message(QueueUrl=p.queue_url, ReceiptHandle=handle)
            case ExecuteResult.Retry:
                # 可視性タイムアウトを0に設定して即時再処理可能にする
                logger.debug(
                    "Change message visibility",
                    extra={"queue": p.queue_url, "handle": handle},
                )
                sqs.change_message_visibility(
                    QueueUrl=p.queue_url, ReceiptHandle=handle, VisibilityTimeout=0
                )
            case ExecuteResult.SendDLQ:
                body = message.pop("Body", "")
                kwargs = {}
                attribute = message.get("Attributes", {})
                if value := attribute.get("MessageGroupId"):
                    kwargs["MessageGroupId"] = value
                if value := attribute.get("MessageDeduplicationId", ""):
                    kwargs["MessageDeduplicationId"] = value
                logger.debug(
                    "Send DLQ",
                    extra={
                        "queue": p.queue_url,
                        "handle": handle,
                        "dead_later_queue": p.dead_later_queue_url,
                    },
                )
                # DLQへ送信
                sqs.send_message(
                    QueueUrl=p.dead_later_queue_url, MessageBody=body, **kwargs
                )
                # 現在のメッセージを削除
                sqs.delete_message(QueueUrl=p.queue_url, ReceiptHandle=handle)
    else:
        missing_receipt_handle.send(result_type=result, message=message)
        raise ValueError("Missing ReceiptHandle.")


def _get_message_attribute_value(
    value: MessageAttributeValueTypeDef,
) -> str | bytes | list[str] | list[bytes] | None:
    """
    StringValue
    BinaryValue
    StringListValues
    BinaryListValues
    """
    return value.get(
        "StringValue",
        value.get(
            "BinaryValue",
            value.get("StringListValues", value.get("BinaryListValues", None)),
        ),
    )
