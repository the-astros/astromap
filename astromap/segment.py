"""
implements constellation segmentation algorithm

edge_brightness = (((a.magnitude + b.magnitude) ** magnitude_power)
+ ((distance(a, b) * distance_coefficient) ** distance_power))

edge_priority = edge_brightness + (rival_coefficient / rival_brightness)

To find the distance between two polar coordinates on a unit sphere,
use the formula:

arccos(sin(φ1)sin(φ2) + cos(φ1)cos(φ2)cos(θ2 - θ1))

where φ1 and φ2 are the zenith angles (latitude-like) and θ1 and θ2 are the
azimuthal angles (longitude-like) of the two points; this formula essentially
calculates the angle between the two points on the sphere, which is the
shortest distance between them on the unit sphere surface.
"""

import logging
import numpy as np
import math

from astromap import bright


class Param:
    """
    parameter set to segment the sky into groups of stars
    - values stored internally as ints (& str for version)
    - two parameters with same field values will have same hash value
    """

    def __init__(
        self,
        version: str = "v0.5.0",  # semantic version of segmenter
        count: int = 300,  # number of stars to draft over
        magnitude_offset: float = 1.5,
        magnitude_power: float = 1.0,
        distance_power: float = 2.0,
        distance_coefficient: float = 2.0**10,
        rival_power: float = 2.0,
        rival_coefficient: float = 2.0**32,
        row: tuple[int, str, int, int, int, int, int, int, int] | None = None,
    ) -> None:
        # if row of db values is given initialize from row
        if row is not None:
            (
                self._hsh,
                self._version,
                self._count,
                self._magnitude_offset_cent,
                self._magnitude_power_cent,
                self._distance_power_cent,
                self._distance_coefficient,
                self._rival_power_cent,
                self._rival_coefficient,
            ) = row
            return

        # otherwise convert floats to ints & generate hash
        self._version: str = version
        self._count: int = count
        self._magnitude_offset_cent: int = math.floor(magnitude_offset * 100)
        self._magnitude_power_cent: int = math.floor(magnitude_power * 100)
        self._distance_power_cent: int = math.floor(distance_power * 100)
        self._distance_coefficient: int = math.floor(distance_coefficient)
        self._rival_power_cent: int = math.floor(rival_power * 100)
        self._rival_coefficient: int = math.floor(rival_coefficient)
        self._hsh: int = hash(
            (
                self._version,
                self._count,
                self._magnitude_offset_cent,
                self._magnitude_power_cent,
                self._distance_power_cent,
                self._distance_coefficient,
                self._rival_power_cent,
                self._rival_coefficient,
            )
        )

    def __hash__(self) -> int:
        return self._hsh

    @property
    def version(self) -> str:
        return self._version

    @property
    def count(self) -> int:
        return self._count

    @property
    def magnitude_offset(self) -> float:
        return float(self._magnitude_offset_cent / 100)

    @property
    def magnitude_power(self) -> float:
        return float(self._magnitude_power_cent / 100)

    @property
    def distance_power(self) -> float:
        return float(self._distance_power_cent / 100)

    @property
    def distance_coefficient(self) -> float:
        return float(self._distance_coefficient)

    @property
    def rival_power(self) -> float:
        return float(self._rival_power_cent / 100)

    @property
    def rival_coefficient(self) -> float:
        return float(self._rival_coefficient)

    def row(self) -> tuple[int, str, int, int, int, int, int, int, int]:
        """
        return values as a tuple to write to db table
        """
        return (
            self._hsh,
            self._version,
            self._count,
            self._magnitude_offset_cent,
            self._magnitude_power_cent,
            self._distance_power_cent,
            self._distance_coefficient,
            self._rival_power_cent,
            self._rival_coefficient,
        )


def visit(
    param: Param, stars: list[bright.Star]
) -> tuple[list[bright.Group], list[bright.Sky]]:
    """
    apply param values to segment stars into a series of groups and skies
    """

    pairwise_magnitudes: np.ndarray = _get_magnitude_matrix(stars)
    distances: np.ndarray = _get_distance_matrix(stars)

    #
    # vectorized calculation of prominence from pairwise magnitudes & distances
    #
    prominences = np.add(
        np.power(
            pairwise_magnitudes + (2 * param.magnitude_offset),
            param.magnitude_power,
        ),
        np.power(
            np.multiply(distances, param.distance_coefficient),
            param.distance_power,
        ),
    )

    # initialize matrix of rival prominences for each edge to calculate shadows
    # - shadows are only calculated once for each edge where u < v
    # - all shadow edges where u >= v are initialized to infinity
    # - edges where u < v are initialized to prominence value
    rivals: np.ndarray = np.zeros(prominences.shape, dtype=np.float64)
    shadows: np.ndarray = np.full(prominences.shape, np.inf, dtype=np.float64)
    for u, v in np.ndindex(shadows.shape):
        if u < v:
            shadows[u, v] = prominences[u, v]

    logging.debug(f"initial rivals:\n{rivals}")

    # draft edges by minimum shadow prominence until
    # - all stars are drafted and
    # - all edges are merged into one group
    skies: list[bright.Sky] = []
    lonely_stars: set[int] = set(range(param.count))
    grouped_stars: dict[int, int] = {}  # sorted index: group number
    star_groups: dict[int, set[int]] = {}  # group number: set of star indices
    visited_groups: dict[int, bright.Group] = {}  # star index set hash: group
    next_draft: int = 0
    next_group: int = 0
    while next_draft < (2**16) and (
        len(lonely_stars) > 0 or len(star_groups) > 1
    ):
        next_draft += 1

        # find next minimum shadow prominence in matrix
        u, v = (
            int(i) for i in np.unravel_index(np.argmin(shadows), shadows.shape)
        )

        logging.debug(f"draft {next_draft}: ({u}, {v})")

        # remove stars from lonely stars set
        lonely_stars.discard(u)
        lonely_stars.discard(v)

        # determine group for new edge from groups of stars in pair
        # - if both stars are grouped
        #   * if groups are same do nothing
        #   * if groups are different merge groups to min group
        # - if one star is grouped add to existing group
        # - if neither star is grouped create new group with next group number
        group_number: int | None = None

        # if neither is grouped create new group
        if u not in grouped_stars and v not in grouped_stars:
            group_number = next_group
            next_group += 1
            star_groups[group_number] = set()

        # if both are grouped and in different groups merge groups
        elif u in grouped_stars and v in grouped_stars:
            if grouped_stars[u] != grouped_stars[v]:
                merge_number: int = max(grouped_stars[u], grouped_stars[v])
                group_number = min(grouped_stars[u], grouped_stars[v])

                merge_group: set[int] = star_groups[merge_number]
                star_groups[group_number] |= star_groups[merge_number]
                star_groups.pop(merge_number)
                for star_index in merge_group:
                    grouped_stars[star_index] = group_number

        # if only one is in group add to that group
        elif u in grouped_stars:
            group_number = grouped_stars[u]
        elif v in grouped_stars:
            group_number = grouped_stars[v]

        logging.debug(
            f"draft {next_draft}:"
            f" edge ({stars[u].catalog}, {stars[v].catalog})"
            f" group {group_number}"
            f" prominence {prominences[u, v]:.1f}"
            f" shadow {shadows[u, v]:.1f}"
        )

        # mark this edges shadow as infinity to prevent it being picked again
        shadows[u, v] = np.inf

        # if we have a group number
        # - add group index to stars
        # - add star indices to new group
        # - mark rivals
        if group_number is not None:
            grouped_stars[u] = group_number
            grouped_stars[v] = group_number
            star_groups[group_number].add(u)
            star_groups[group_number].add(v)

            # collect group hashes for sky
            group_hashes: set[int] = set()
            for star_group in star_groups.values():
                # get hash of group set indexed by brightness
                star_group_hash: int = hash(frozenset(star_group))

                # if group isnt already indexed by star index hash create it
                # - proper group has sets of stars by catalog index
                if star_group_hash not in visited_groups:
                    catalog_group: frozenset[int] = frozenset(
                        (stars[i].catalog for i in star_group)
                    )
                    group: bright.Group = bright.Group(
                        hsh=hash(catalog_group), stars=catalog_group
                    )
                    visited_groups[star_group_hash] = group

                group: bright.Group = visited_groups[star_group_hash]
                group_hashes.add(hash(group))

            # build sky from group hashes
            frozen_hashes: frozenset[int] = frozenset(group_hashes)
            sky: bright.Sky = bright.Sky(
                hsh=hash(frozen_hashes), groups=frozen_hashes
            )
            skies.append(sky)

            # mark rivals and then recalculate shadows
            # - multiply distance by coefficent to minimize rival penalty for
            #   very near neighbors
            # - mark rivals in both directions ([u, v] + [v, u]) so we can
            #   get all rivals by summing a column
            rival_prominence: float = (
                (distances[u, v] ** param.rival_power)
                * param.rival_coefficient
                / prominences[u, v]
            )
            rivals[u, v] = rival_prominence
            rivals[v, u] = rival_prominence

            # get sum of all rivals to each star and then add together with
            # the prominence to get each shadowed prominence
            rival_sums = np.sum(rivals, axis=0)

            # recalculate shadows for all edges that share a star with current
            # edge and havent been drafted
            for u_ in range(shadows.shape[0]):
                shadow_edge = (u_, v) if u_ < v else (v, u_)
                if shadows[shadow_edge] < np.inf:
                    # print(f"old shadow {shadow_edge}: {shadows[shadow_edge]}")
                    shadows[shadow_edge] = (
                        prominences[shadow_edge]
                        + rival_sums[u_]
                        + rival_sums[v]
                    )
                    # print(f"new shadow {shadow_edge}: {shadows[shadow_edge]}")
            for v_ in range(shadows.shape[1]):
                shadow_edge = (u, v_) if u < v_ else (v_, u)
                if shadows[shadow_edge] < np.inf:
                    # print(f"old shadow {shadow_edge}: {shadows[shadow_edge]}")
                    shadows[shadow_edge] = (
                        prominences[shadow_edge]
                        + rival_sums[u]
                        + rival_sums[v_]
                    )
                    # print(f"new shadow {shadow_edge}: {shadows[shadow_edge]}")

    if len(lonely_stars) > 0:
        raise RuntimeError(
            f"ran out of draft steps with {len(lonely_stars)} stars left"
        )
    if len(star_groups) > 1:
        raise RuntimeError(
            f"ran out of draft steps with {len(star_groups)} groups unmerged"
        )

    # return lists of groups & skies visited during segmentation
    groups: list[bright.Group] = list(visited_groups.values())
    return groups, skies


def _get_magnitude_matrix(stars: list[bright.Star]) -> np.ndarray:
    """vectorized calculation of pairwise magnitude"""

    magnitudes = np.array(
        [star.magnitude for star in stars],
        dtype=float,
    )

    mags = magnitudes.reshape(1, len(stars))
    pairwise_magnitudes = mags + mags.T

    return pairwise_magnitudes


def _get_distance_matrix(stars: list[bright.Star]) -> np.ndarray:
    """vectorized calculation of distance"""

    coords = np.array(
        [[star.coords[0], star.coords[1]] for star in stars],
        dtype=float,
    )
    ras = coords[:, 0].reshape(1, len(stars))
    declinations = coords[:, 1].reshape(1, len(stars))

    dec_sin = np.sin(declinations)
    pairwise_dec_sin = dec_sin * dec_sin.T

    dec_cos = np.cos(declinations)
    pairwise_dec_cos = dec_cos * dec_cos.T
    ras_delta = np.abs(ras - ras.T)

    pairwise_ra_diff_cos = np.cos(
        np.minimum(ras_delta, (2 * np.pi) - ras_delta)
    )

    distances = np.arccos(
        np.minimum(
            1.0,
            pairwise_dec_sin + (pairwise_dec_cos * pairwise_ra_diff_cos),
        )
    )

    return distances
