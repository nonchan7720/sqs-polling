from enum import IntEnum, auto


class ExecuteResult(IntEnum):
    Nil = auto()
    Deletable = auto()
    Retry = auto()
    Reject = auto()
    SendDLQ = auto()

    def __str__(self) -> str:
        match self:
            case ExecuteResult.Nil:
                return "Nil"
            case ExecuteResult.Deletable:
                return "Deletable"
            case ExecuteResult.Retry:
                return "Retry"
            case ExecuteResult.Reject:
                return "Reject"
            case ExecuteResult.SendDLQ:
                return "SendDLQ"
            case _:
                return "Missing"
