import pytest

from demo.core import Widget, _clip


@pytest.mark.spec("widget-edge", "Edge widgets have a size")
class TestEdgeWidget:
    def test_size_needs_compute(self):
        w = Widget("a")
        with pytest.raises(RuntimeError, match="first"):
            w.size()

    def test_size_raises_before_compute(self):
        with pytest.raises(RuntimeError):
            Widget("a").size()

    def test_path_kept(self):
        w = Widget("a")
        assert w.only_tests_call_this() == "a"


@pytest.mark.spec("widget-node", "Node widgets have a size")
class TestNodeWidget:
    def test_size_needs_compute(self):
        w = Widget("b")
        with pytest.raises(RuntimeError, match="first"):
            w.size()

    def test_path_kept(self):
        w = Widget("b")
        assert w.only_tests_call_this() == "b"


def test_clip_low():
    values = [1, 2, 3]
    out = _clip(values, 2, 3)
    assert out == [2, 2, 3]
    assert len(out) == 3


def test_clip_high():
    values = [4, 5, 6]
    out = _clip(values, 0, 5)
    assert out == [4, 5, 5]
    assert len(out) == 3


def test_clip_none():
    values = [7, 8, 9]
    out = _clip(values, 0, 10)
    assert out == [7, 8, 9]
    assert len(out) == 3


def test_reads_private_cache():
    w = Widget("c")
    assert w._cache is None
