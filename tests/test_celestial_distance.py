import math

import pytest

from astromap.star import CelestialCoordinates, celestial_distance

a: CelestialCoordinates = CelestialCoordinates(
    right_ascension=0.25 * math.pi, declination=0.25 * math.pi
)
b: CelestialCoordinates = CelestialCoordinates(
    right_ascension=0.25 * math.pi, declination=0
)
c: CelestialCoordinates = CelestialCoordinates(
    right_ascension=0.25 * math.pi, declination=-0.25 * math.pi
)
e: CelestialCoordinates = CelestialCoordinates(
    right_ascension=math.pi, declination=0
)
h: CelestialCoordinates = CelestialCoordinates(
    right_ascension=1.5 * math.pi, declination=0
)
k: CelestialCoordinates = CelestialCoordinates(
    right_ascension=1.75 * math.pi, declination=0
)


def test_a_b() -> None:
    assert celestial_distance(a, b) == pytest.approx(0.25 * math.pi)


def test_a_c() -> None:
    assert celestial_distance(a, c) == pytest.approx(0.5 * math.pi)


def test_b_e() -> None:
    assert celestial_distance(b, e) == pytest.approx(0.75 * math.pi)


def test_b_h() -> None:
    assert celestial_distance(b, h) == pytest.approx(0.75 * math.pi)


def test_b_k() -> None:
    assert celestial_distance(b, k) == pytest.approx(0.5 * math.pi)
