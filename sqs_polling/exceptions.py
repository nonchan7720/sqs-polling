class BasePollingException(Exception):
    """Base"""

    pass


class RetryException(BasePollingException):
    """
    VisibleTimeoutを0に設定してメッセージを再処理する
    Set VisibleTimeout to 0 to reprocess messages
    """

    pass


class RejectException(BasePollingException):
    """
    処理できないメッセージを削除する
    Delete messages that cannot be processed
    """

    pass


class RejectDLQException(BasePollingException):
    """
    処理できないメッセージをDLQへ送信し、メッセージを削除する
    Sends messages that cannot be processed to DLQ and deletes messages
    """

    pass
