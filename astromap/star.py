from dataclasses import dataclass
from enum import StrEnum
from operator import eq
from typing import Final, TypeAlias
import math


class DeclinationSign(StrEnum):
    NEGATIVE = "-"
    POSITIVE = "+"


@dataclass
class EquatorialCoordinates:
    # hours, minutes, seconds
    right_ascension: tuple[float, float, float]

    # sign, degrees, arcminutes, arcseconds
    declination: tuple[DeclinationSign, float, float, float]


@dataclass
class PolarCoordinates:
    """
    equatorial coordinates expressed in radians

    - azimuth is radians in range [0 - 2pi)
    - zenith is in range [0 - pi] offset from the positive z axis
    """

    azimuth: float
    zenith: float


@dataclass
class ProperMotion:
    right_ascension: float
    declination: float


@dataclass
class BrightStar:
    """
    parameters of a star from the bright star catalog

    - all coordinates in the j2000 epoch in the fk5 reference frame
    """

    number: int  # bright star catalog number
    name: str | None
    magnitude: float  # apparent visual magnitude
    coords: PolarCoordinates
    motion: PolarCoordinates  # proper motion / year expressed in polar coords
    equatorial: EquatorialCoordinates
    proper: ProperMotion
    spectral: str | None  # spectral type


def polar_from_equatorial(eq_coords: EquatorialCoordinates) -> PolarCoordinates:
    """
    convert equatorial coordinates to polar coordinates
    """
    # converts hours, minutes, seconds to degrees and then to radians
    # 1 hour = 15 degrees
    # 1 second = 15 / 3600 degrees
    azimuth: float = math.radians(
        (
            (eq_coords.right_ascension[0] * 3600)  # hours to seconds
            + (eq_coords.right_ascension[1] * 60)  # minutes to seconds
            + eq_coords.right_ascension[2]  # already seconds
        )
        * (15 / 3600)  # seconds to degrees
    )

    # convert degrees, minutes, seconds to digital degrees and then to radians
    zenith: float = math.radians(
        eq_coords.declination[1]  # already degrees
        + (
            (
                (eq_coords.declination[2] * 60)  # minutes to seconds
                + eq_coords.declination[3]  # already seconds
            )
        )
        * (15 / 3600)  # seconds to degrees
    )

    # convert offset from equator to north pole
    if eq_coords.declination[0] is DeclinationSign.NEGATIVE:
        zenith += math.pi * 0.5  # negative declination is offset from pi / 2
    else:
        zenith = (math.pi * 0.5) - zenith  # subtract +declination from pi / 2

    return PolarCoordinates(azimuth=azimuth, zenith=zenith)


def polar_from_proper(proper: ProperMotion) -> PolarCoordinates:
    """
    convert proper motion to polar coordinates
    """
    azimuth: float = math.radians(proper.right_ascension / 3600)
    zenith: float = math.radians(proper.declination / -3600)

    return PolarCoordinates(azimuth=azimuth, zenith=zenith)


# these catalog entries have been partially removed as they are not stars
NOT_STARS: set[int] = set(
    [
        92,
        95,
        182,
        1057,
        1841,
        2472,
        2496,
        3515,
        3671,
        6309,
        6515,
        7189,
        7539,
        8296,
    ]
)


def star_from_catalog(row: str) -> BrightStar | None:
    """parse star data from row of bright star catalog"""
    if len(row) < 170:
        return None

    number: int = int(row[0:4], base=10)

    if number in NOT_STARS:
        return None

    try:
        name: str | None = (
            " ".join(row[4:14].strip().split())
            if len(row[4:14].strip()) > 0
            else None
        )
        equatorial: EquatorialCoordinates = EquatorialCoordinates(
            right_ascension=(
                float(row[75:77]),
                float(row[77:79]),
                float(row[79:83]),
            ),
            declination=(
                DeclinationSign(row[83]),
                float(row[84:86]),
                float(row[86:88]),
                float(row[88:90]),
            ),
        )
        magnitude: float = float(row[102:107])
        spectral: str | None = row[127:147].strip()
        if len(spectral) < 1:
            spectral = None
        proper: ProperMotion = ProperMotion(
            float(row[148:154]),
            float(row[154:160]),
        )

    except ValueError as error:
        print(f"failed to parse row: {row} \n\t{error}")
        return None

    return BrightStar(
        number=number,
        name=name,
        magnitude=magnitude,
        coords=polar_from_equatorial(equatorial),
        motion=polar_from_proper(proper),
        equatorial=equatorial,
        proper=proper,
        spectral=spectral,
    )
