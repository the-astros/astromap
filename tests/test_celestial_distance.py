import math

import pytest

from astromap import bright

a: tuple[float, float] = (0.25 * math.pi, 0.25 * math.pi)
b: tuple[float, float] = (0.25 * math.pi, 0)
c: tuple[float, float] = (0.25 * math.pi, -0.25 * math.pi)
e: tuple[float, float] = (math.pi, 0)
h: tuple[float, float] = (1.5 * math.pi, 0)
k: tuple[float, float] = (1.75 * math.pi, 0)


def test_a_b() -> None:
    assert bright.celestial_distance(a, b) == pytest.approx(0.25 * math.pi)


def test_a_c() -> None:
    assert bright.celestial_distance(a, c) == pytest.approx(0.5 * math.pi)


def test_b_e() -> None:
    assert bright.celestial_distance(b, e) == pytest.approx(0.75 * math.pi)


def test_b_h() -> None:
    assert bright.celestial_distance(b, h) == pytest.approx(0.75 * math.pi)


def test_b_k() -> None:
    assert bright.celestial_distance(b, k) == pytest.approx(0.5 * math.pi)
