from dataclasses import dataclass
from enum import StrEnum
from typing import Final, TypeAlias


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
    equatorial: EquatorialCoordinates
    proper: ProperMotion
    spectral: str | None  # spectral type


def star_from_catalog(row: str) -> BrightStar | None:
    """parse star data from row of bright star catalog"""
    if len(row) < 170:
        return None

    try:
        number: int = int(row[0:4], base=10)
        name: str | None = (
            " ".join(row[4:14].strip().split()) if len(row[4:14].strip()) > 0 else None
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
        equatorial=equatorial,
        proper=proper,
        spectral=spectral,
    )
