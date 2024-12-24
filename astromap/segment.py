"""
implements constellation segmentation algorithm

edge_brightness = (((a.magnitude + b.magnitude) ** magnitude_power)
+ ((distance(a, b) ** distance_power) ** distance_coefficient))

edge_priority = 

To find the distance between two polar coordinates on a unit sphere,
use the formula:

arccos(sin(φ1)sin(φ2) + cos(φ1)cos(φ2)cos(θ2 - θ1))

where φ1 and φ2 are the zenith angles (latitude-like) and θ1 and θ2 are the
azimuthal angles (longitude-like) of the two points; this formula essentially
calculates the angle between the two points on the sphere, which is the
shortest distance between them on the unit sphere surface.
"""

from operator import attrgetter
import numpy as np

from astromap.star import BrightStar
from astromap.catalog import BrightStarCatalog


class SkySegmenter:
    def __init__(self, catalog: BrightStarCatalog) -> None:
        self._catalog: BrightStarCatalog = catalog

        self._magnitude_power: np.float64 = np.float64(2.0)
        self._distance_power: np.float64 = np.float64(2.0)
        self._distance_coefficient: np.float64 = np.float64(16.0)

        self._numbers: list[int] | None = None
        self._magnitudes: np.ndarray | None = None
        self._coords: np.ndarray | None = None
        self._pairwise_magnitudes: np.ndarray | None = None
        self._distances: np.ndarray | None = None
        self._brights: np.ndarray | None = None

    def segment(self, max_magnitude: float = 2.0) -> list[tuple[int, int]]:
        edges: list[tuple[int, int]] = []

        # get list of stars below given magnitude & sorted by magnitude
        stars = sorted(
            [star for star in self._catalog if star.magnitude <= max_magnitude],
            key=attrgetter("magnitude"),
        )

        # break up star attributes into a list of star #s & two numpy arrays
        self._numbers = [star.number for star in stars]
        self._magnitudes = np.array(
            [star.magnitude + 1.5 for star in stars], dtype=float
        )
        self._coords = np.array(
            [[star.coords.azimuth, star.coords.zenith] for star in stars],
            dtype=float,
        )

        # vectorized calculations of pairwise magnitude
        mags = self._magnitudes.reshape(1, self._magnitudes.size)
        self._pairwise_magnitudes = mags + mags.T

        # vectorized calculations of distance
        azimuths = self._coords[:, 0].reshape(1, self._coords.shape[0])
        zeniths = self._coords[:, 1].reshape(1, self._coords.shape[0])

        zn_sin = np.sin(zeniths)
        pairwise_zn_sin = zn_sin * zn_sin.T

        zn_cos = np.cos(zeniths)
        pairwise_zn_cos = zn_cos * zn_cos.T

        pairwise_az_diff_cos = np.cos(azimuths - azimuths.T)

        self._distances = np.arccos(
            pairwise_zn_sin + (pairwise_zn_cos * pairwise_az_diff_cos)
        )

        # 

        return edges

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
