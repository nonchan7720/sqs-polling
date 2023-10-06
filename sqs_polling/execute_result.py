from enum import IntEnum, auto


class ExecuteResult(IntEnum):
    Nil = auto()
    Deletable = auto()
    Retry = auto()
    Reject = auto()
    SendDLQ = auto()
