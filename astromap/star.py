from dataclasses import InitVar, dataclass
from enum import StrEnum
from typing import Final, TypeAlias


class MultipleStarCode(StrEnum):
    A = "A"  # Astrometric binary
    D = "D"  # Duplicity discovered by occultation
    I = "I"  # Innes, Southern Double Star Catalogue (1927)
    R = "R"  # Rossiter, Michigan Publ. 9, 1955
    S = "S"  # Duplicity discovered by speckle interferometry
    W = "W"  # Worley (1978) update of the IDS


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


GalacticCoordinates: TypeAlias = tuple[float, float]  # longitude, latitude


@dataclass
class BrightStar:
    number: int  # bright star catalog number
    name: str | None
    multiple: MultipleStarCode | None
    b1900: EquatorialCoordinates
    j2000: EquatorialCoordinates
    j2000_motion: ProperMotion
    galactic: GalacticCoordinates
    magnitude: float  # visual magnitude
    spectral: str | None  # spectral type


def star_from_catalog(row: str) -> BrightStar | None:
    """parse star data from row of bright star catalog"""
    if len(row) < 170:
        return None

    try:
        number: int = int(row[0:4], base=10)
        name: str | None = (
            row[4:14].strip() if len(row[4:14].strip()) > 0 else None
        )
        multiple: MultipleStarCode | None = (
            MultipleStarCode(row[43]) if row[43] in MultipleStarCode else None
        )
        b1900: EquatorialCoordinates = EquatorialCoordinates(
            right_ascension=(
                float(row[60:62]),
                float(row[62:64]),
                float(row[64:68]),
            ),
            declination=(
                DeclinationSign(row[68]),
                float(row[69:71]),
                float(row[71:73]),
                float(row[73:75]),
            ),
        )
        j2000: EquatorialCoordinates = EquatorialCoordinates(
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
        galactic: GalacticCoordinates = GalacticCoordinates(
            (
                float(row[90:96]),
                float(row[96:102]),
            )
        )
        magnitude: float = float(row[102:107])
        spectral: str | None = row[127:147].strip()
        if len(spectral) < 1:
            spectral = None
        j2000_motion: ProperMotion = ProperMotion(
            float(row[148:154]),
            float(row[154:160]),
        )

    except ValueError as error:
        print(f"failed to parse row: {row} \n\t{error}")
        return None

    return BrightStar(
        number=number,
        name=name,
        multiple=multiple,
        b1900=b1900,
        j2000=j2000,
        j2000_motion=j2000_motion,
        galactic=galactic,
        magnitude=magnitude,
        spectral=spectral,
    )
