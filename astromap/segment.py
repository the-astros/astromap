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
from typing import Self
import numpy as np

from astromap.star import BrightStar
from astromap.catalog import BrightStarCatalog


@dataclass
class BrightEdge:
    index: tuple[int, int]  # indices of this edge into ndarray
    stars: tuple[int, int]  # catalog numbers of vertex stars
    brightness: float  # brightness metric
    now_bright: float  # brightness + rival_brightness
    rival: tuple[int, int] | None = None
    rival_brightness: float | None = None

    def __lt__(self, other: object) -> bool:
        if other is None:
            return True
        if isinstance(other, self.__class__):
            return self.now_bright < other.now_bright
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if other is None:
            return True
        if isinstance(other, self.__class__):
            return self.now_bright <= other.now_bright
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):
            return self.now_bright > other.now_bright
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):
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

        self._edges: np.ndarray | None = None

    def _gen_edges(self, max_magnitude: float = 2.0) -> None:
        # get list of stars below given magnitude & sorted by magnitude
        stars = sorted(
            [star for star in self._catalog if star.magnitude <= max_magnitude],
            key=attrgetter("magnitude"),
        )

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
        azimuths = coords[:, 0].reshape(1, len(stars))
        zeniths = coords[:, 1].reshape(1, len(stars))

        zn_sin = np.sin(zeniths)
        pairwise_zn_sin = zn_sin * zn_sin.T

        zn_cos = np.cos(zeniths)
        pairwise_zn_cos = zn_cos * zn_cos.T

        pairwise_az_diff_cos = np.cos(azimuths - azimuths.T)

        distances = np.arccos(
            np.minimum(1.0, pairwise_zn_sin + (pairwise_zn_cos * pairwise_az_diff_cos))
        )

        # vectorized calculation of brightness
        brights = np.add(
            np.power(pairwise_magnitudes, self._magnitude_power),
            np.multiply(
                np.power(distances, self._distance_power),
                self._distance_coefficient,
            ),
        )

        self._edges = np.array(
            [
                BrightEdge(
                    index=(u, v),
                    stars=(numbers[u], numbers[v]),
                    brightness=brights[u, v],
                    now_bright=brights[u, v],
                )
                if u < v
                else None
                for u in range(len(stars))
                for v in range(len(stars))
            ]
        ).reshape(len(stars), len(stars))

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
