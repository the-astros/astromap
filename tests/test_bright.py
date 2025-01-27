import math

import pytest

from astromap import bright


happy_row: str = (
    r"1948 50Zet OriBD-02 1338  37742132444    I   4263A  2553    "
    r"053542.7-015943054045.5-015634206.45-16.59 2.05H -0.21 -1.07"
    r" -0.20   O9.7Ib            e+0.003-0.002 +.024+018SB    140 "
    r" 2.2   2.4AB   3*"
)

happy_star: bright.Star = bright.Star(
    catalog=1948,
    magnitude=2.05,
    coords=(1.4868387175687527, -0.03390786885680094),
    motion=(1.454441043328608e-08, -9.696273622190719e-09),
)

not_a_star_row: str = (
    r" 182 M 31  And                                     S And    "
    r"                                                                                                                                        *"
)


def test_happy_star_from_row() -> None:
    star: bright.Star | None = bright.star_from_catalog(happy_row)
    assert star == happy_star


def test_not_a_star_from_row() -> None:
    star: bright.Star | None = bright.star_from_catalog(not_a_star_row)
    assert star is None
