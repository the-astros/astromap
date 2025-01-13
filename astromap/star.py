from collections.abc import Iterator
from dataclasses import dataclass, field
import math


@dataclass
class CelestialCoordinates:
    """
    equatorial coordinates expressed in radians

    - right ascension is radians in range [0 - 2pi)
    - declination is in range [-pi/2 - pi/2]
    """

    right_ascension: float
    declination: float

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.right_ascension
        if index == 1:
            return self.declination
        raise IndexError(f"index '{index}' out of range [0 - 1]")

    def __iter__(self) -> Iterator[float]:
        yield self.right_ascension
        yield self.declination

    def __post_init__(self) -> None:
        """validate that celestial coordinates are within range of sphere"""

        if self.right_ascension < 0 or 2 * math.pi <= self.right_ascension:
            raise ValueError(
                f"right ascension '{self.right_ascension}'"
                " not in range [0 - 2 * pi)"
            )
        if self.declination < -math.pi / 2 or math.pi / 2 < self.declination:
            raise ValueError(
                f"declination '{self.declination}'"
                " not in range [-pi / 2 - pi / 2]"
            )


def celestial_distance(a: CelestialCoordinates, b: CelestialCoordinates):
    right_ascension_delta = min(
        abs(a.right_ascension - b.right_ascension),
        2 * math.pi - abs(a.right_ascension - b.right_ascension),
    )
    return math.acos(
        (math.sin(a.declination) * math.sin(b.declination))
        + (
            math.cos(a.declination)
            * math.cos(b.declination)
            * math.cos(right_ascension_delta)
        )
    )

@dataclass
class CelestialMotion:
    """
    proper motion expressed in radians
    """
    right_ascension: float
    declination: float

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.right_ascension
        if index == 1:
            return self.declination
        raise IndexError(f"index '{index}' out of range [0 - 1]")

    def __iter__(self) -> Iterator[float]:
        yield self.right_ascension
        yield self.declination


@dataclass
class BrightStar:
    """
    parameters of a star from the bright star catalog

    - all coordinates in the j2000 epoch in the fk5 reference frame
    """

    number: int  # bright star catalog number
    name: str | None
    magnitude: float  # apparent visual magnitude
    coords: CelestialCoordinates
    motion: CelestialMotion  # proper motion / year
    spectral: str | None  # spectral type


@dataclass
class BrightEdge:
    stars: tuple[int, int]  # catalog numbers of vertex stars
    prominence: float  # metric combining brightness & distance of vertices
    shadow: float  # prominence adjusted for rival edges
    draft: int  # order drafted
    group: int | None = None  # number of group drafted into


@dataclass
class BrightGroup:
    number: int  # unique number for each star group
    stars: frozenset[int]  # catalog numbers of member stars
    edges: frozenset[tuple[int, int]]  # catalog star pairs of member edges


@dataclass
class BrightDraft:
    pick: int
    edge: tuple[int, int]  # index by vertex catalog number
    group: int | None
    prominence: float
    shadow: float
    score: int = 0
    five_plus: int = 0
    ten_plus: int = 0
    max_count: int = 0


@dataclass
class BrightSky:
    # index of stars by catalog number
    stars: dict[int, BrightStar] = field(default_factory=dict)

    # edges by vertex catalog number
    edges: dict[tuple[int, int], BrightEdge] = field(default_factory=dict)

    # groups by draft number
    groups: dict[int, BrightGroup] = field(default_factory=dict)

    # record of edge drafts
    drafts: list[BrightDraft] = field(default_factory=list)

    # score for searching for best sky segmentation
    score: int = -1
    max_draft: int = -1
