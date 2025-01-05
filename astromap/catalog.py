from dataclasses import dataclass
from operator import attrgetter
from typing import Iterator, TextIO
from enum import StrEnum
import math

from astromap.star import BrightStar, CelestialCoordinates, CelestialMotion


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


class BrightStarCatalog:
    """
    catalog of bright stars from the yale bright star catalog
    """

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

    def __init__(self, table: TextIO) -> None:
        self._stars: dict[int, BrightStar] = {}

        for row in table:
            star = self.star_from_catalog(row)
            if star is not None:
                self._stars[star.number] = star

        self._magnitudes: list[tuple[float, int]] = [
            (star.magnitude, star.number)
            for star in sorted(
                self._stars.values(), key=attrgetter("magnitude")
            )
        ]

    def __getitem__(self, i: int) -> BrightStar:
        return self._stars[i]

    def __iter__(self) -> Iterator[BrightStar]:
        return self._stars.values().__iter__()

    def __len__(self) -> int:
        return len(self._stars)

    def bright(self, n: int) -> BrightStar:
        return self._stars[self._magnitudes[n][1]]

    @staticmethod
    def celestial_from_equatorial(
        eq_coords: EquatorialCoordinates,
    ) -> CelestialCoordinates:
        """
        convert equatorial coordinates to polar coordinates
        """
        # converts hours, minutes, seconds to degrees and then to radians
        # 1 hour = 15 degrees
        # 1 second = 15 / 3600 degrees
        right_ascension: float = math.radians(
            (
                (eq_coords.right_ascension[0] * 3600)  # hours to seconds
                + (eq_coords.right_ascension[1] * 60)  # minutes to seconds
                + eq_coords.right_ascension[2]  # already seconds
            )
            * (15 / 3600)  # seconds to degrees
        )

        # convert degrees, minutes, seconds to digital degrees and then to radians
        declination: float = math.radians(
            eq_coords.declination[1]  # already degrees
            + (eq_coords.declination[2] / 60)  # minutes to degrees
            + (eq_coords.declination[3] / 3600)  # seconds to degrees
        )

        # take sign into account
        if eq_coords.declination[0] is DeclinationSign.NEGATIVE:
            declination = -declination

        return CelestialCoordinates(
            right_ascension=right_ascension, declination=declination
        )

    @staticmethod
    def celestial_from_proper(proper: ProperMotion) -> CelestialMotion:
        """
        convert proper motion to polar coordinates
        """
        right_ascension: float = math.radians(proper.right_ascension / 3600)
        declination: float = math.radians(proper.declination / 3600)

        return CelestialMotion(
            right_ascension=right_ascension, declination=declination
        )

    def star_from_catalog(self, row: str) -> BrightStar | None:
        """parse star data from row of bright star catalog"""
        if len(row) < 170:
            return None

        number: int = int(row[0:4], base=10)

        if number in self.NOT_STARS:
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
            coords=self.celestial_from_equatorial(equatorial),
            motion=self.celestial_from_proper(proper),
            spectral=spectral,
        )
