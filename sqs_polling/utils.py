import base64
import json
from typing import Any, Callable, TypeVar


def optional_b64_decode(byte_string):
    try:
        data = base64.b64decode(byte_string)
        if base64.b64encode(data) == byte_string:
            return data
        # else the base64 module found some embedded base64 content
        # that should be ignored.
    except Exception:  # pylint: disable=broad-except
        pass
    return byte_string


DecoderT = EncoderT = Callable[[Any], Any]
T = TypeVar("T")
EncodedT = TypeVar("EncodedT")


_decoders: dict[str, DecoderT] = {
    "bytes": lambda o: o.encode("utf-8"),
    "base64": lambda o: base64.b64decode(o.encode("utf-8")),
}


def object_hook(o: dict):
    if o.keys() == {"__type__", "__value__"}:
        decoder = _decoders.get(o["__type__"])
        if decoder:
            return decoder(o["__value__"])
        else:
            raise ValueError("Unsupported type", type, o)
    else:
        return o


def loads(
    s, _loads=json.loads, decode_bytes=True, object_hook=object_hook
) -> dict[str, Any] | list | tuple:
    if isinstance(s, memoryview):
        s = s.tobytes().decode("utf-8")
    elif isinstance(s, bytearray):
        s = s.decode("utf-8")
    elif decode_bytes and isinstance(s, bytes):
        s = s.decode("utf-8")

    return _loads(s, object_hook=object_hook)


def bytes_to_str(s):
    """Convert bytes to str."""
    if isinstance(s, bytes):
        return s.decode(errors="replace")
    return s
