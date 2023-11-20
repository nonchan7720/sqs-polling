import os
import signal
from asyncio import Future, create_task, get_event_loop
from concurrent.futures import ProcessPoolExecutor as Executor
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from sqs_polling.handler import get_handler
from sqs_polling.polling import _handler, logger, shutdown

from .signal import heartbeat, ready
from .utils import find_module


def _heartbeat_handler(pid: int):
    while True:
        try:
            heartbeat.send()
            sleep(2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(e)
            raise e


def heartbeat_handler():
    def callback(pid: int):
        def _callback(future: Future):
            if future.exception():
                os.kill(pid, signal.SIGTERM)

        return _callback

    pid = os.getpid()
    loop = get_event_loop()
    executor = Executor(max_workers=1)
    future = loop.run_in_executor(executor, _heartbeat_handler, pid)
    future.add_done_callback(callback(pid))


def handler(func_name: str, **kwargs) -> Executor | ThreadPoolExecutor:
    func_names = func_name.split(".")
    module_name = ".".join(func_names[:-1])
    _ = find_module(module_name)
    name = func_names[-1]
    p = get_handler(name)
    p.update(**kwargs)
    return _handler(p)


def main(func_name: str, **kwargs) -> None:
    executor = handler(func_name, **kwargs)
    ready.send()
    heartbeat_handler()
    loop = get_event_loop()
    for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            s,
            lambda s=s: create_task(shutdown(loop=loop, executor=executor, signal=s)),
        )
    loop.run_forever()
    loop.close()
