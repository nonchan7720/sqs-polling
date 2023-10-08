from typing import Callable, Generic, TypeVar

TConnectHandle = TypeVar("TConnectHandle", bound=Callable)


class Signal(Generic[TConnectHandle]):
    def __init__(self, name: str, *args, **kwargs) -> None:
        self.name = name
        self.__handlers: list[TConnectHandle] = []
        self.__args = args
        self.__kwargs = kwargs

    def connect(self, handler: TConnectHandle):
        self.__handlers.append(handler)

    def disconnect(self, handler: TConnectHandle):
        self.__handlers.remove(handler)

    def send(self):
        for handler in self.__handlers:
            handler(*self.__args, **self.__kwargs)


ready = Signal("Ready")
heartbeat = Signal("Heartbeat")
shutdown = Signal("Shutdown")
