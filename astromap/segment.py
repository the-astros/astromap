"""
implements constellation segmentation algorithm

edge_brightness = (((a.magnitude + b.magnitude) ** magnitude_power)
+ ((distance(a, b) ** distance_power) ** distance_coefficient))

edge_priority = edge_brightness + (rival_coefficient / rival_brightness)

To find the distance between two polar coordinates on a unit sphere,
use the formula:

arccos(sin(φ1)sin(φ2) + cos(φ1)cos(φ2)cos(θ2 - θ1))

where φ1 and φ2 are the zenith angles (latitude-like) and θ1 and θ2 are the
azimuthal angles (longitude-like) of the two points; this formula essentially
calculates the angle between the two points on the sphere, which is the
shortest distance between them on the unit sphere surface.
"""

from dataclasses import dataclass
from operator import attrgetter
from os import sep
from typing import Self
import numpy as np

from astromap.star import BrightStar
from astromap.catalog import BrightStarCatalog


@dataclass
class BrightEdge:
    index: tuple[int, int]  # indices of this edge into ndarray
    stars: tuple[int, int]  # catalog numbers of vertex stars
    brightness: float  # brightness metric
    now_bright: float | None  # brightness + rival_brightness
    rival: tuple[int, int] | None = None
    rival_brightness: float | None = None
    group: int | None = None  # which group this edge belongs to

    def __lt__(self, other: object) -> bool:
        if other is None:
            return True
        if isinstance(other, self.__class__):
            if self.now_bright is None:
                return False
            if other.now_bright is None:
                return True
            return self.now_bright < other.now_bright
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if other is None:
            return True
        if isinstance(other, self.__class__):
            if other.now_bright is None:
                return True
            if self.now_bright is None:
                return False
            return self.now_bright <= other.now_bright
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):
            if other.now_bright is None:
                return False
            if self.now_bright is None:
                return True
            return self.now_bright > other.now_bright
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):
            if self.now_bright is None:
                return True
            if other.now_bright is None:
                return False
            return self.now_bright >= other.now_bright
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):
            return self.now_bright == other.now_bright
        return NotImplemented


class SkySegmenter:
    def __init__(self, catalog: BrightStarCatalog) -> None:
        self._catalog: BrightStarCatalog = catalog

        self._magnitude_power: np.float64 = np.float64(2.0)
        self._distance_power: np.float64 = np.float64(2.0)
        self._distance_coefficient: np.float64 = np.float64(16.0)
        self._rival_coefficient: np.float64 = np.float64(16.0)

        self._numbers: list[int] = []  # catalog number by index into edges
        self._edges: np.ndarray | None = None
        self._groups: list[set[tuple[int, int]]] = []
        self._members: dict[int, int] = {}  # star_index: group_index

    def segment(self, max_magnitude: float = 2.0) -> None:
        numbers, edges = self._gen_edges(max_magnitude=max_magnitude)

        count: int = len(numbers)

        self._numbers = numbers
        self._edges = edges
        self._groups = []
        self._members = {}

        lonely_stars: set[int] = set([i for i in range(count)])

        while len(lonely_stars) > 0:
            brightest: tuple[int, ...] = tuple(
                [
                    int(i)
                    for i in np.unravel_index(np.argmin(edges), edges.shape)
                ]
            )
            assert len(brightest) == 2

            edge: BrightEdge = self._edges[brightest]

            group_index: int | None = None
            separate_groups: bool = False
            group: set[tuple[int, int]] = set()
            for i in brightest:

                # check if either star is already in a group
                if i in self._members:

                    # if both vertices of edge are already in separate groups
                    # dont add this edge to either
                    if group_index is not None:
                        if group_index != self._members[i]:
                            separate_groups = True

                    group_index = self._members[i]

            edge.now_bright = None
            if not separate_groups:

                if group_index is None:
                    group_index = len(self._groups)
                    self._groups.append(group)
                else:
                    group = self._groups[group_index]

                group.add(brightest)
                edge.group = group_index

                # remove stars from lonely stars set 
                # & add group to members index
                for i in brightest:

                    # remove both vertices from lonely stars set
                    lonely_stars.discard(i)
                    self._members[i] = group_index


    def _gen_edges(
        self, max_magnitude: float = 2.0
    ) -> tuple[list[int], np.ndarray]:
        # get list of stars below given magnitude & sorted by magnitude
        stars = sorted(
            [star for star in self._catalog if star.magnitude <= max_magnitude],
            key=attrgetter("magnitude"),
        )
        count = len(stars)

        # break up star attributes into a list of star #s & two numpy arrays
        numbers: list[int] = [star.number for star in stars]
        magnitudes = np.array(
            [star.magnitude + 1.5 for star in stars], dtype=float
        )
        coords = np.array(
            [[star.coords.azimuth, star.coords.zenith] for star in stars],
            dtype=float,
        )

        # vectorized calculation of pairwise magnitude
        mags = magnitudes.reshape(1, magnitudes.size)
        pairwise_magnitudes = mags + mags.T

        # vectorized calculation of distance
        azimuths = coords[:, 0].reshape(1, count)
        zeniths = coords[:, 1].reshape(1, count)

        zn_sin = np.sin(zeniths)
        pairwise_zn_sin = zn_sin * zn_sin.T

        zn_cos = np.cos(zeniths)
        pairwise_zn_cos = zn_cos * zn_cos.T

        pairwise_az_diff_cos = np.cos(azimuths - azimuths.T)

        distances = np.arccos(
            np.minimum(
                1.0, pairwise_zn_sin + (pairwise_zn_cos * pairwise_az_diff_cos)
            )
        )

        # vectorized calculation of brightness
        brights = np.add(
            np.power(pairwise_magnitudes, self._magnitude_power),
            np.multiply(
                np.power(distances, self._distance_power),
                self._distance_coefficient,
            ),
        )

        edges = np.array(
            [
                BrightEdge(
                    index=(u, v),
                    stars=(numbers[u], numbers[v]),
                    brightness=brights[u, v],
                    now_bright=brights[u, v],
                )
                if u < v
                else None
                for u in range(count)
                for v in range(count)
            ]
        ).reshape(count, count)

        return numbers, edges

    @staticmethod
    def distance(
        aa: np.float64, az: np.float64, ba: np.float64, bz: np.float64
    ) -> np.float64:
        """calculate angular distance between two points on unit sphere

        with polar coords (azimuth, zenith) for two points on the sphere a, b:
        aa: azimuth a
        az: zenith a
        ba: azimuth b
        bz: zenith b

        distance = arccos(sin(az)sin(bz) + cos(az)cos(bz)cos(ba - aa))
        """
        return np.arccos(
            (np.sin(az) * np.sin(bz))
            + (np.cos(az) * np.cos(bz) * np.cos(ba - aa))
        )
