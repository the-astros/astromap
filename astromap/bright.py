from dataclasses import dataclass
import logging
import math


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


@dataclass
class Star:
    """
    star from the bright star catalog

    - all coordinates in the j2000 epoch in the fk5 reference frame
    """

    catalog: int  # bright star catalog index
    magnitude: float  # apparent visual magnitude
    coords: tuple[float, float]  # right ascension, declination
    motion: tuple[float, float]  # proper motion / year

    def __post_init__(self) -> None:
        """validate that celestial coordinates are within range of sphere"""

        if self.coords[0] < 0 or 2 * math.pi <= self.coords[0]:
            raise ValueError(
                f"right ascension '{self.coords[0]}'"
                " not in range [0 - 2 * pi)"
            )
        if self.coords[1] < -math.pi / 2 or math.pi / 2 < self.coords[1]:
            raise ValueError(
                f"declination '{self.coords[1]}'"
                " not in range [-pi / 2 - pi / 2]"
            )


def star_from_catalog(row: str) -> Star | None:
    """parse star data from row of bright star catalog"""
    if len(row) < 170:
        return None

    catalog: int = int(row[0:4], base=10)

    if catalog in NOT_STARS:
        return None

    try:
        equatorial_right_ascension: tuple[float, float, float] = (
            float(row[75:77]),
            float(row[77:79]),
            float(row[79:83]),
        )
        equatorial_declination: tuple[bool, float, float, float] = (
            True if "+" == row[83] else False,
            float(row[84:86]),
            float(row[86:88]),
            float(row[88:90]),
        )
        magnitude: float = float(row[102:107])
        proper_right_ascension: float = float(row[148:154])
        proper_declination: float = float(row[154:160])

        return Star(
            catalog=catalog,
            magnitude=magnitude,
            coords=celestial_from_equatorial(
                equatorial_right_ascension, equatorial_declination
            ),
            motion=celestial_from_proper(
                proper_right_ascension, proper_declination
            ),
        )

    except ValueError as error:
        logging.warning(f"failed to parse row: {row} \n\t{error}")
        return None


def celestial_from_equatorial(
    # hours, minutes, seconds
    equatorial_right_ascension: tuple[float, float, float],
    # sign, degrees, arcminutes, arcseconds
    equatorial_declination: tuple[bool, float, float, float],
) -> tuple[float, float]:
    """
    convert equatorial coordinates to polar coordinates
    """
    # converts hours, minutes, seconds to degrees and then to radians
    # 1 hour = 15 degrees
    # 1 second = 15 / 3600 degrees
    right_ascension: float = math.radians(
        (
            (equatorial_right_ascension[0] * 3600)  # hours to seconds
            + (equatorial_right_ascension[1] * 60)  # minutes to seconds
            + equatorial_right_ascension[2]  # already seconds
        )
        * (15 / 3600)  # seconds to degrees
    )

    # convert degrees, minutes, seconds to digital degrees and then to radians
    declination: float = math.radians(
        equatorial_declination[1]  # already degrees
        + (equatorial_declination[2] / 60)  # minutes to degrees
        + (equatorial_declination[3] / 3600)  # seconds to degrees
    )

    # take sign into account
    if not equatorial_declination[0]:
        declination = -declination

    return (right_ascension, declination)


def celestial_from_proper(
    proper_right_ascension: float, proper_declination: float
) -> tuple[float, float]:
    """
    convert proper motion to polar coordinates
    """
    right_ascension: float = math.radians(proper_right_ascension / 3600)
    declination: float = math.radians(proper_declination / 3600)

    return (right_ascension, declination)


def celestial_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """
    takes two sets of celestial coords and returns the distance in radians

    a: tuple[float, float] -> [right_ascension, declination] in radians
    b: tuple[float, float] -> [right_ascension, declination] in radians

    returns: angular distance between a and b in radians
    """
    right_ascension_delta = min(
        abs(a[0] - b[0]),
        2 * math.pi - abs(a[0] - b[0]),
    )
    return math.acos(
        (math.sin(a[1]) * math.sin(b[1]))
        + (math.cos(a[1]) * math.cos(b[1]) * math.cos(right_ascension_delta))
    )


@dataclass
class Group:
    """
    a group of neighboring stars that form a constellation
    """

    hsh: int  # hash of stars frozenset
    stars: frozenset[int]  # set of bright star catalog numbers

    def __hash__(self) -> int:
        return self.hsh


@dataclass
class Sky:
    """
    a grouping of stars into constellations
    """

    hsh: int  # hash of groups frozenset
    groups: frozenset[int]  # set of group hashes

    def __hash__(self) -> int:
        return self.hsh
