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
from sys import displayhook
from typing import Self
import numpy as np

from astromap.star import (
    BrightStar,
    BrightEdge,
    BrightGroup,
    BrightDraft,
    BrightSky,
)
from astromap.catalog import BrightStarCatalog


def segment(
    stars: list[BrightStar],
    magnitude_power: float = 1.0,
    distance_power: float = 2.0,
    distance_coefficient: float = 512.0,
    rival_coefficient: float = 16.0,
) -> BrightSky:
    """segment stars into groups by brightness & distance"""
    sky: BrightSky = BrightSky()

    # add stars to sky by catalog number
    for star in stars:
        sky.stars[star.number] = star

    # get list of stars ordered from lowest to highest magnitude
    # - lower magnitude is brighter
    sorted_stars: list[BrightStar] = sorted(stars, key=attrgetter("magnitude"))

    # print("sorted stars:")
    # for i, star in enumerate(sorted_stars):
    #     print(f"{i}: {star}")

    # get matrix of edge prominences (where lowest value is most prominent)
    prominences: np.ndarray = _get_prominence_matrix(
        sorted_stars,
        magnitude_power=magnitude_power,
        distance_power=distance_power,
        distance_coefficient=distance_coefficient,
    )

    # initialize matrix of rival prominences for each edge to calculate shadows
    # - shadows are only calculated once for each edge where u < v
    # - all rival edges where u >= v are initialized to infinity
    # - edges where u < v are initialized to zero
    rivals: np.ndarray = np.full(prominences.shape, np.inf, dtype=np.float64)
    for u, v in np.ndindex(prominences.shape):
        if u < v:
            rivals[u, v] = 0.0
    shadows = prominences + rivals

    # print("rivals:")
    # print(rivals)

    # print("shadows:")
    # print(shadows)

    # draft edges by minimum shadow prominence until all stars are drafted
    lonely_stars: set[int] = set(range(len(sorted_stars)))
    grouped_stars: dict[int, int] = {}  # sorted index: group number
    grouped_edges: dict[tuple[int, int], int] = {}  # edge tuple: group number
    groups: dict[int, set[tuple[int, int]]] = {}
    next_draft: int = 0
    next_group: int = 0
    while len(lonely_stars) > 0 and next_draft < (2**16):
        # find next minimum shadow prominence in matrix
        u, v = (
            int(i) for i in np.unravel_index(np.argmin(shadows), shadows.shape)
        )

        catalog_edge: tuple[int, int] = (
            sorted_stars[u].number,
            sorted_stars[v].number,
        )

        # print(f"draft {next_draft}: ({u}, {v})")

        # remove stars from lonely stars set
        lonely_stars.discard(u)
        lonely_stars.discard(v)

        # determine group for new edge from groups of stars in pair
        # - if both stars are grouped merge groups to min group
        # - if one star is grouped add to existing group
        # - if neither star is grouped create new group with next group number
        group_number: int | None = (
            None if u not in grouped_stars else grouped_stars[u]
        )
        if v in grouped_stars:
            if group_number is None:
                group_number = grouped_stars[v]

            # if both stars are in different groups merge to minimum
            if group_number != grouped_stars[v]:
                merge_group_number: int = max(group_number, grouped_stars[v])
                group_number = min(group_number, grouped_stars[v])

                merge_group: set[tuple[int, int]] = groups[merge_group_number]
                groups[group_number] |= groups[merge_group_number]
                groups.pop(merge_group_number)
                for p, q in merge_group:
                    grouped_stars[p] = group_number
                    grouped_stars[q] = group_number
                    grouped_edges[p, q] = group_number
                    merge_catalog_edge: tuple[int, int] = (
                        sorted_stars[p].number,
                        sorted_stars[q].number,
                    )
                    sky.edges[merge_catalog_edge].group = group_number

        if group_number is None:
            group_number = next_group
            next_group += 1
            groups[group_number] = set()

        # add this edge to stars & groups
        grouped_stars[u] = group_number
        grouped_stars[v] = group_number
        grouped_edges[u, v] = group_number
        groups[group_number].add((u, v))

        # record draft
        draft = BrightDraft(
            pick=next_draft,
            edge=catalog_edge,
            group=group_number,
            prominence=prominences[u, v],
            shadow=shadows[u, v],
        )
        next_draft += 1
        sky.drafts.append(draft)

        # create edge
        edge = edge = BrightEdge(
            stars=draft.edge,
            prominence=draft.prominence,
            shadow=draft.shadow,
            draft=draft.pick,
            group=draft.group,
        )
        sky.edges[edge.stars] = edge

        # mark this edges rival as infinity to prevent it being picked again
        rivals[u, v] = np.inf
        shadows[u, v] = np.inf

        # print(draft)

    if lonely_stars:
        raise RuntimeError(
            f"ran out of draft steps with {len(lonely_stars)} stars left"
        )

    # build groups
    for group_number, group in groups.items():
        group_stars: set[int] = set()
        group_edges: set[tuple[int, int]] = set()
        for edge in group:
            group_catalog_edge: tuple[int, int] = (
                sorted_stars[edge[0]].number,
                sorted_stars[edge[1]].number,
            )
            group_stars |= set(group_catalog_edge)
            group_edges.add(group_catalog_edge)
        bright_group = BrightGroup(
            number=group_number,
            stars=frozenset(group_stars),
            edges=frozenset(group_edges),
        )
        sky.groups[bright_group.number] = bright_group

    return sky


def _get_prominence_matrix(
    sorted_stars: list[BrightStar],
    magnitude_power: float,
    distance_power: float,
    distance_coefficient: float,
) -> np.ndarray:
    """get matrix of edge prominences (where lowest value is most prominent)

    prominence is calculated from:
    - sum of brightness magnitude of each star in pair (lower is brighter)
    - distance between stars (greater distance reduces prominence)
    """
    count: int = len(sorted_stars)

    #
    # vectorized calculation of pairwise magnitude"""
    #

    magnitudes = np.array(
        [star.magnitude + 1.5 for star in sorted_stars], dtype=float
    )

    mags = magnitudes.reshape(1, count)
    pairwise_magnitudes = mags + mags.T

    #
    # vectorized calculation of distance
    #

    coords = np.array(
        [
            [star.coords.right_ascension, star.coords.declination]
            for star in sorted_stars
        ],
        dtype=float,
    )
    ras = coords[:, 0].reshape(1, count)
    declinations = coords[:, 1].reshape(1, count)

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

    #
    # vectorized calculation of prominence
    #
    prominences = np.add(
        np.power(pairwise_magnitudes, magnitude_power),
        np.multiply(
            np.power(distances, distance_power),
            distance_coefficient,
        ),
    )

    return prominences
