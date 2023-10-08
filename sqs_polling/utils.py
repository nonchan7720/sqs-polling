import base64
import json
import os
import sys
from contextlib import contextmanager
from importlib import import_module
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


@contextmanager
def cwd_in_path():
    """Context adding the current working directory to sys.path."""
    try:
        cwd = os.getcwd()
    except FileNotFoundError:
        cwd = None
    if not cwd:
        yield
    elif cwd in sys.path:
        yield
    else:
        sys.path.insert(0, cwd)
        try:
            yield cwd
        finally:
            try:
                sys.path.remove(cwd)
            except ValueError:  # pragma: no cover
                pass


class NotAPackage(Exception):
    """Raised when importing a package, but it's not a package."""


def find_module(module, path=None, imp=None):
    """Version of :func:`imp.find_module` supporting dots."""
    if imp is None:
        imp = import_module
    with cwd_in_path():
        try:
            return imp(module)
        except ImportError:
            # Raise a more specific error if the problem is that one of the
            # dot-separated segments of the module name is not a package.
            if "." in module:
                parts = module.split(".")
                for i, part in enumerate(parts[:-1]):
                    package = ".".join(parts[: i + 1])
                    try:
                        mpart = imp(package)
                    except ImportError:
                        # Break out and re-raise the original ImportError
                        # instead.
                        break
                    try:
                        mpart.__path__
                    except AttributeError:
                        raise NotAPackage(package)
            raise
