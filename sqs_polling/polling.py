from __future__ import annotations

import queue
import signal
import sys
from asyncio import all_tasks, create_task, current_task, gather, get_event_loop
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, thread
from functools import wraps
from logging import getLogger
from threading import Event
from typing import TYPE_CHECKING, Any, Callable

import boto3

from sqs_polling.exceptions import RetryException
from sqs_polling.utils import bytes_to_str, loads, optional_b64_decode

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from mypy_boto3_sqs import SQSClient
    from mypy_boto3_sqs.type_defs import MessageTypeDef

ev = Event()
logger = getLogger(__name__)
_handlers: dict[str, dict[str, Any]] = {}


async def shutdown(
    loop, executor: ProcessPoolExecutor | ThreadPoolExecutor, signal=None
) -> None:
    if signal:
        logger.info(f"received exit signal {signal.name}...")

    py_version = sys.version_info
    if (py_version.major == 3) and (py_version.minor < 9):
        executor.shutdown(wait=False)
        work_item: thread._WorkItem | None = None
        while True:
            try:
                if isinstance(executor, ThreadPoolExecutor):
                    work_item = executor._work_queue.get_nowait()
            except queue.Empty:
                break
            if work_item is not None:
                work_item.future.cancel()
    else:
        executor.shutdown(cancel_futures=True)
    tasks = [t for t in all_tasks() if t is not current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"cancelling {len(tasks)} outstanding tasks")

    await gather(*tasks, return_exceptions=True)
    logger.info("cancelled tasks")

    loop.stop()
    logger.info("gracefully shutdown the service.")


def polling(
    queue_url: str,
    visibility_timeout: int,
    exception_deletable: bool = False,
    interval_seconds: float = 1.0,
    max_workers: int = 1,
    max_number_of_messages: int = 1,
    process_worker: bool = False,
    aws_profile: dict[str, Any] = {},
) -> Callable:
    def inner(func: Callable):
        @wraps(func)
        def _inner():
            _handlers[func.__name__] = {
                "func": func,
                "queue_url": queue_url,
                "visibility_timeout": visibility_timeout,
                "exception_deletable": exception_deletable,
                "interval_seconds": interval_seconds,
                "max_workers": max_workers,
                "max_number_of_messages": max_number_of_messages,
                "process_worker": process_worker,
                "aws_profile": aws_profile,
            }

        return _inner()

    return inner


_session: SQSClient | None = None


def _get_session(aws_profile_dict: dict[str, Any]) -> SQSClient:
    global _session

    if _session is None:
        _session = boto3.client("sqs", **aws_profile_dict)

    return _session


def _handler(
    func: Callable,
    queue_url: str,
    visibility_timeout: int,
    exception_deletable: bool = False,
    interval_seconds: float = 1.0,
    max_workers: int = 1,
    max_number_of_messages: int = 1,
    process_worker: bool = False,
    aws_profile: dict[str, Any] = {},
):
    with ProcessPoolExecutor(
        max_workers=max_workers
    ) if process_worker else ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = get_event_loop()
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                s,
                lambda s=s: create_task(
                    shutdown(loop=loop, executor=executor, signal=s)
                ),
            )
        loop.call_soon(
            _polling,
            loop,
            executor,
            func,
            queue_url,
            visibility_timeout,
            exception_deletable,
            interval_seconds,
            max_number_of_messages,
            aws_profile,
        )
        loop.run_forever()
        loop.close()


def _polling(
    loop: AbstractEventLoop,
    executor: ThreadPoolExecutor | ProcessPoolExecutor,
    func: Callable,
    queue_url: str,
    visibility_timeout: int,
    exception_deletable: bool = False,
    interval_seconds: float = 1.0,
    max_number_of_messages: int = 1,
    aws_profile_dict: dict[str, Any] = {},
):
    def _submit(message: MessageTypeDef):
        f = executor.submit(
            _execute,
            queue_url,
            func,
            message,
            exception_deletable,
            aws_profile_dict,
        )
        return f

    sqs = _get_session(aws_profile_dict)
    messages = _sqs_receive(sqs, queue_url, visibility_timeout, max_number_of_messages)
    if len(messages) > 0:
        [_submit(message) for message in messages]
    loop.call_later(
        interval_seconds,
        _polling,
        loop,
        executor,
        queue_url,
        visibility_timeout,
        func,
        exception_deletable,
        interval_seconds,
        max_number_of_messages,
        aws_profile_dict,
    )


def _sqs_receive(
    sqs: SQSClient, queue_url: str, visibility_timeout: int, max_number_of_messages=1
):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        VisibilityTimeout=visibility_timeout,
        MaxNumberOfMessages=max_number_of_messages,
    )
    if "Messages" in response:
        messages = [m for m in response["Messages"]]
    else:
        messages = []

    return messages


def _execute(
    queue_url: str,
    func: Callable,
    message: MessageTypeDef,
    exception_deletable: bool,
    aws_profile_dict: dict[str, Any],
):
    body = optional_b64_decode(message.get("Body", "{}").encode())
    payload = loads(bytes_to_str(body))
    deletable = False
    try:
        if isinstance(payload, dict):
            func(**payload)
        elif isinstance(payload, list) or isinstance(payload, tuple):
            func(*payload)
        deletable = True
    except RetryException:
        deletable = False
    except Exception:
        deletable = exception_deletable

    if deletable:
        sqs = _get_session(aws_profile_dict)
        sqs.delete_message(
            QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]  # type: ignore
        )
