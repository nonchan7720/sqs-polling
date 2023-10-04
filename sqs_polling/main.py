from sqs_polling.polling import _handler, _handlers


def main(func_name: str, **kwargs) -> None:
    handle = _handlers[func_name]
    handle.update(**kwargs)
    _handler(**handle)
