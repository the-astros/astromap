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

from dataclasses import dataclass
from operator import attrgetter
from os import sep
from sys import displayhook
from typing import Self
import numpy as np
import math

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
    magnitude_offset: float = 1.5,
    magnitude_power: float = 1.0,
    distance_power: float = 2.0,
    distance_coefficient: float = 4.0,
    rival_coefficient: float = 16.0,
) -> BrightSky:
    """segment stars into groups by brightness & distance"""
    print(
        f"segment-v0.4.0(star_count={len(stars)}"
        f", magnitude_offset={magnitude_offset:.1f}"
        f", magnitude_power={magnitude_power:.1f}"
        f", distance_power={distance_power:.1f}"
        f", distance_coefficient={distance_coefficient:.1f}"
        f", rival_coefficient={rival_coefficient:.1f})"
    )
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

    pairwise_magnitudes: np.ndarray = _get_magnitude_matrix(sorted_stars)
    distances: np.ndarray = _get_distance_matrix(sorted_stars)

    #
    # vectorized calculation of prominence from pairwise magnitudes & distances
    #
    prominences = np.add(
        np.power(pairwise_magnitudes + (2 * magnitude_offset), magnitude_power),
        np.power(
            np.multiply(distances, distance_coefficient),
            distance_power,
        ),
    )

    # initialize matrix of rival prominences for each edge to calculate shadows
    # - shadows are only calculated once for each edge where u < v
    # - all rival edges where u >= v are initialized to infinity
    # - edges where u < v are initialized to zero
    rivals: np.ndarray = np.zeros(prominences.shape, dtype=np.float64)
    shadows: np.ndarray = np.full(prominences.shape, np.inf, dtype=np.float64)
    for u, v in np.ndindex(shadows.shape):
        if u < v:
            shadows[u, v] = prominences[u, v]

    # print("initial rivals:")
    # print(rivals)

    # print("initial shadows:")
    # print(shadows)

    # draft edges by minimum shadow prominence until all stars are drafted
    lonely_stars: set[int] = set(range(len(sorted_stars)))
    grouped_stars: dict[int, int] = {}  # sorted index: group number
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
        group_number: int | None = None

        # if neither is grouped create new group
        if u not in grouped_stars and v not in grouped_stars:
            group_number = next_group
            next_group += 1
            groups[group_number] = set()

        # if both are grouped and in different groups merge groups
        elif u in grouped_stars and v in grouped_stars:
            if grouped_stars[u] != grouped_stars[v]:
                merge_number: int = max(grouped_stars[u], grouped_stars[v])
                group_number = min(grouped_stars[u], grouped_stars[v])

                merge_group: set[tuple[int, int]] = groups[merge_number]
                groups[group_number] |= groups[merge_number]
                groups.pop(merge_number)
                for p, q in merge_group:
                    grouped_stars[p] = group_number
                    grouped_stars[q] = group_number
                    merge_catalog_edge: tuple[int, int] = (
                        sorted_stars[p].number,
                        sorted_stars[q].number,
                    )
                    sky.edges[merge_catalog_edge].group = group_number

        # if only one is in group add to that group
        elif u in grouped_stars:
            group_number = grouped_stars[u]
        elif v in grouped_stars:
            group_number = grouped_stars[v]

        # record draft
        draft: BrightDraft = BrightDraft(
            pick=next_draft,
            edge=catalog_edge,
            group=group_number,
            prominence=prominences[u, v],
            shadow=shadows[u, v],
        )
        next_draft += 1
        sky.drafts.append(draft)

        # if we have a group number create edge
        if group_number is not None:
            grouped_stars[u] = group_number
            grouped_stars[v] = group_number
            groups[group_number].add((u, v))
            edge = BrightEdge(
                stars=draft.edge,
                prominence=draft.prominence,
                shadow=draft.shadow,
                draft=draft.pick,
                group=draft.group,
            )
            sky.edges[edge.stars] = edge

            # calculate draft score
            group_count: dict[int, int] = {}  # sorted index: star count
            for group in grouped_stars.values():
                if group not in group_count:
                    group_count[group] = 0
                group_count[group] += 1
            for count in group_count.values():
                if count > draft.max_count:
                    draft.max_count = count
                if count >= 5:
                    draft.score += 1
                    draft.five_plus += 1
                if count >= 10:
                    draft.score += 1
                    draft.ten_plus += 1
                if count >= 15:
                    draft.score += 1
                if count >= 20:
                    draft.score -= 2
                if count >= 25:
                    draft.score -= 5
                if count >= 30:
                    draft.score -= 10
                if count >= 35:
                    draft.score -= 10
                if count >= 40:
                    draft.score -= 10
            if draft.score > sky.score:
                sky.score = draft.score
                sky.max_draft = draft.pick

        # mark this edges shadow as infinity to prevent it being picked again
        shadows[u, v] = np.inf

        # mark rivals and then recalculate shadows
        # - multiply distance by coefficent to minimize rival penalty for very
        #   near neighbors
        # - mark rivals in both directions ([u, v] + [v, u]) so we can
        #   get all rivals by summing a column
        rival_prominence: float = (
            (distances[u, v] ** 2.0) * rival_coefficient / prominences[u, v]
        )
        rivals[u, v] = rival_prominence
        rivals[v, u] = rival_prominence

        # get sum of all rivals to each star and then add together with
        # the prominence to get each shadowed prominence
        rival_sums = np.sum(rivals, axis=0)

        # recalculate shadows for all edges that share a star with current edge
        # and havent been drafted
        for u_ in range(shadows.shape[0]):
            shadow_edge = (u_, v) if u_ < v else (v, u_)
            if shadows[shadow_edge] < np.inf:
                # print(f"old shadow {shadow_edge}: {shadows[shadow_edge]}")
                shadows[shadow_edge] = (
                    prominences[shadow_edge] + rival_sums[u_] + rival_sums[v]
                )
                # print(f"new shadow {shadow_edge}: {shadows[shadow_edge]}")
        for v_ in range(shadows.shape[1]):
            shadow_edge = (u, v_) if u < v_ else (v_, u)
            if shadows[shadow_edge] < np.inf:
                # print(f"old shadow {shadow_edge}: {shadows[shadow_edge]}")
                shadows[shadow_edge] = (
                    prominences[shadow_edge] + rival_sums[u] + rival_sums[v_]
                )
                # print(f"new shadow {shadow_edge}: {shadows[shadow_edge]}")

        # print(draft)

    if len(lonely_stars) > 0:
        raise RuntimeError(
            f"ran out of draft steps with {len(lonely_stars)} stars left"
        )

    # for u, v in np.ndindex(prominences.shape):
    #     if u < v:
    #         print(f"{u}, {v}: {prominences[u, v]} -> {shadows[u, v]}")


    # build groups up to edges found at max draft score
    for group_number, group in groups.items():
        group_stars: set[int] = set()
        group_edges: set[tuple[int, int]] = set()
        for edge in group:
            group_catalog_edge: tuple[int, int] = (
                sorted_stars[edge[0]].number,
                sorted_stars[edge[1]].number,
            )
            # only add edges up to max draft pick & remove rest
            if sky.edges[group_catalog_edge].draft <= sky.max_draft:
                group_stars |= set(group_catalog_edge)
                group_edges.add(group_catalog_edge)
            else:
                sky.edges.pop(group_catalog_edge)
        bright_group = BrightGroup(
            number=group_number,
            stars=frozenset(group_stars),
            edges=frozenset(group_edges),
        )
        sky.groups[bright_group.number] = bright_group

    max_draft = sky.drafts[sky.max_draft]
    print(f"sky score: {sky.score} max draft: {max_draft.pick}"
        f" max count: {max_draft.max_count}"
        f" fives: {max_draft.five_plus} tens: {max_draft.ten_plus}")

    return sky


def _get_magnitude_matrix(sorted_stars: list[BrightStar]) -> np.ndarray:
    """vectorized calculation of pairwise magnitude"""

    magnitudes = np.array(
        [star.magnitude for star in sorted_stars],
        dtype=float,
    )

    mags = magnitudes.reshape(1, len(sorted_stars))
    pairwise_magnitudes = mags + mags.T

    return pairwise_magnitudes


def _get_distance_matrix(sorted_stars: list[BrightStar]) -> np.ndarray:
    """vectorized calculation of distance"""

    coords = np.array(
        [
            [star.coords.right_ascension, star.coords.declination]
            for star in sorted_stars
        ],
        dtype=float,
    )
    ras = coords[:, 0].reshape(1, len(sorted_stars))
    declinations = coords[:, 1].reshape(1, len(sorted_stars))

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
