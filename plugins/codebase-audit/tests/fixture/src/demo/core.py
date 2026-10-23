"""Fixture package with one planted instance of every pattern the scripts find."""

from typing import Literal

Policy = Literal["warn", "strict"]


def _clip(values, low, high):
    out = []
    for v in values:
        if v < low:
            v = low
        elif v > high:
            v = high
        out.append(v)
    return out


def _bound(items, floor, ceiling):
    result = []
    for x in items:
        if x < floor:
            x = floor
        elif x > ceiling:
            x = ceiling
        result.append(x)
    return result


def load(path, policy: Policy = "warn", mode: str = "region"):
    """Load a widget.

    Parameters
    ----------
    path : str
        Where to read from.
    policy : {"warn", "ignore"}
        What to do on a mismatch.
    mode : str
        Region or dense.
    extra : int
        Not a parameter at all.
    """
    if mode == "dense":
        raise NotImplementedError("dense mode is not supported")
    return Widget(path)


class Widget:
    def __init__(self, path):
        self._path = path
        self._cache = None

    def size(self):
        if self._cache is None:
            raise RuntimeError("call compute() first")
        return len(self._cache)

    def dense_size(self, dense=False):
        if dense:
            raise ValueError("not supported for a dense parcellation")
        return 0

    def only_tests_call_this(self):
        """A public method nothing in the package calls."""
        return self._path


try:
    import networkx  # noqa: F401
except ImportError:
    networkx = None
