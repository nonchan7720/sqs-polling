from typing import Callable, Generic, TypeVar

TConnectHandle = TypeVar("TConnectHandle", bound=Callable)


class Signal(Generic[TConnectHandle]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.__handlers: list[TConnectHandle] = []

    def connect(self, handler: TConnectHandle):
        self.__handlers.append(handler)

    def disconnect(self, handler: TConnectHandle):
        self.__handlers.remove(handler)

    def send(self, *args, **kwargs):
        for handler in self.__handlers:
            handler(*args, **kwargs)


ready = Signal("Ready")
heartbeat = Signal("Heartbeat")
shutdown = Signal("Shutdown")
handler_result = Signal("HandlerResult")
missing_receipt_handle = Signal("MissingReceiptHandle")
