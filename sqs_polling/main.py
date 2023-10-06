import os
import signal
import time
from asyncio import get_event_loop
from concurrent.futures import ProcessPoolExecutor as Executor
from importlib import import_module
from logging import getLogger

from sqs_polling.handler import get_handler
from sqs_polling.polling import _handler

from .signal import heartbeat, ready

logging = getLogger(__name__)


def _heartbeat_handler(pid: int):
    while True:
        try:
            heartbeat.send()
            time.sleep(2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(e)
            os.kill(pid, signal.SIGTERM)
            break


def heartbeat_handler():
    pid = os.getpid()
    loop = get_event_loop()
    executor = Executor(max_workers=1)
    loop.run_in_executor(executor, _heartbeat_handler, pid)


def main(func_name: str, **kwargs) -> None:
    func_names = func_name.split(".")
    module_name = ".".join(func_names[:-1])
    _ = import_module(module_name)
    name = func_names[-1]
    p = get_handler(name)
    p.update(**kwargs)
    ready.send()
    heartbeat_handler()
    _handler(p)
