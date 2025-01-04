from dataclasses import dataclass
from enum import StrEnum


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
