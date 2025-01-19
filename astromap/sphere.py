from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Iterator, TextIO
import json
import logging
import math

import sqlite3

from astromap import bright


@dataclass
class Group:
    hsh: int  # hash of stars frozenset
    stars: frozenset[int]  # set of bright star catalog numbers
    rating: int  # rating of this group

    def __hash__(self) -> int:
        return self.hsh


@dataclass
class Sky:
    hsh: int  # hash of groups frozenset
    groups: frozenset[int]  # set of group hashes
    rating: int  # sum of ratings of groups

    def __hash__(self) -> int:
        return self.hsh


class Parameter:
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
        distance_coefficient: float = 2.0 ** 10,
        rival_power: float = 2.0,
        rival_coefficient: float = 2.0 ** 32,
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


@dataclass
class Draft:
    """
    a draft of skies held with a given set of parameters
    """

    param_hash: int  # segment parameter hash is also primary key
    rating: int  # highest rating of drafted skies
    top_draft: int | None  # index into sky draft picks with max rating
    skies: tuple[int, ...]  # draft list of sky hashes to full merge

    def __hash__(self) -> int:
        return self.param_hash


def create_tables(conn: sqlite3.Connection) -> None:
    cursor: sqlite3.Cursor = conn.cursor()

    # create stars table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS stars (
        catalog INTEGER PRIMARY KEY,
        magnitude REAL,
        coords_0 REAL,
        coords_1 REAL,
        motion_0 REAL,
        motion_1 REAL
    )
"""
    )

    # index stars by brightness magnitude
    cursor.execute(
        """
    CREATE INDEX brightness_index ON stars (magnitude)
"""
    )

    # create groups table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS groups (
        hsh INTEGER PRIMARY KEY,
        stars TEXT,
        rating INTEGER
    )
"""
    )

    # index groups by rating
    cursor.execute(
        """
    CREATE INDEX group_rating_index ON groups (rating)
"""
    )

    # create skies table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS skies (
        hsh INTEGER PRIMARY KEY,
        groups TEXT,
        rating INTEGER
    )
"""
    )

    # index skies by rating
    cursor.execute(
        """
    CREATE INDEX sky_rating_index ON skies (rating)
"""
    )

    # create parameters table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS parameters (
        hsh INTEGER PRIMARY KEY,
        version TEXT,
        count INTEGER,
        magnitude_offset INTEGER,
        magnitude_power INTEGER,
        distance_power INTEGER,
        distance_coefficient INTEGER,
        rival_power INTEGER,
        rival_coefficient INTEGER
    )
"""
    )

    # create drafts table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS drafts (
        param_hash INTEGER PRIMARY KEY,
        rating INTEGER,
        top_draft INTEGER,
        skies TEXT
    )
"""
    )
    conn.commit()


def select_all_stars(conn: sqlite3.Connection) -> list[bright.Star]:
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """
    SELECT catalog, magnitude, coords_0, coords_1, motion_0, motion_1
    FROM stars
    ORDER BY magnitude
"""
    )
    rows = cursor.fetchall()
    stars = [
        bright.Star(row[0], row[1], (row[2], row[3]), (row[4], row[5]))
        for row in rows
    ]
    return stars


def import_catalog(conn: sqlite3.Connection, table: TextIO) -> None:
    cursor: sqlite3.Cursor = conn.cursor()

    stars: list[bright.Star] = []
    for row in table:
        star: bright.Star | None = bright.star_from_catalog(row)
        if star is not None:
            stars.append(star)

    cursor.executemany(
        """
INSERT INTO stars (
    catalog, magnitude, coords_0, coords_1, motion_0, motion_1
)
VALUES (?, ?, ?, ?, ?, ?)
""",
        [
            (
                star.catalog,
                star.magnitude,
                star.coords[0],
                star.coords[1],
                star.motion[0],
                star.motion[1],
            )
            for star in stars
        ],
    )

    conn.commit()


def select_parameter_by_hash(
    conn: sqlite3.Connection, hsh: int
) -> Parameter | None:
    parameter: Parameter | None = None
    cursor: sqlite3.Cursor = conn.cursor()

    cursor.execute(
        """
    SELECT (
        hsh,
        version,
        count,
        magnitude_offset,
        magnitude_power,
        distance_power,
        distance_coefficient,
        rival_power,
        rival_coefficient
    )
    FROM drafts
    WHERE hsh = ?
""",
        (hsh,),
    )
    row = cursor.fetchone()
    if row is not None:
        parameter = Parameter(row=row)
    return parameter


def select_draft_by_param_hash(
    conn: sqlite3.Connection, param_hash: int
) -> Draft | None:
    draft: Draft | None = None
    cursor: sqlite3.Cursor = conn.cursor()

    cursor.execute(
        """
    SELECT param_hash, rating, top_draft, skies
    FROM drafts
    WHERE param_hash = ?
""",
        (param_hash,),
    )
    row = cursor.fetchone()
    if row is not None:
        draft = Draft(
            param_hash=row[0],
            rating=row[1],
            top_draft=row[2] if row[2] != 0 else None,
            skies=tuple(json.loads(row[3])),
        )
    return draft


def draft_skies(conn: sqlite3.Connection, parameter: Parameter) -> Draft:
    cursor: sqlite3.Cursor = conn.cursor()

    # check if given parameters are already drafted
    draft: Draft | None = select_draft_by_param_hash(conn, hash(parameter))

    if draft is not None:
        return draft

    # insert parameter into table (if it doesnt exist)
    cursor.execute(
        """
INSERT OR IGNORE INTO parameters (
    hsh,
    version,
    count,
    magnitude_offset,
    magnitude_power,
    distance_power,
    distance_coefficient,
    rival_power,
    rival_coefficient
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
        parameter.row(),
    )

    conn.commit()

    skies: list[Sky] = []


    # build draft from skies
    top_rating: int = 0
    top_draft: int | None = None
    sky_hashes: list[int] = []
    for i, sky in enumerate(skies):
        sky_hashes.append(hash(sky))
        if sky.rating > top_rating:
            top_rating = sky.rating
            top_draft = i

    draft = Draft(
        param_hash=hash(parameter),
        rating=top_rating,
        top_draft=top_draft,
        skies=tuple(sky_hashes),
    )

    return draft

def segment(parameter: Parameter) -> BrightSky:
    """segment stars into groups by brightness & distance"""
    print(
        f"segment-v0.4.0(star_count={len(sorted_stars)}"
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

def _get_magnitude_matrix(sorted_stars: list[bright.Star]) -> np.ndarray:
    """vectorized calculation of pairwise magnitude"""

    magnitudes = np.array(
        [star.magnitude for star in sorted_stars],
        dtype=float,
    )

    mags = magnitudes.reshape(1, len(sorted_stars))
    pairwise_magnitudes = mags + mags.T

    return pairwise_magnitudes


def _get_distance_matrix(sorted_stars: list[bright.Star]) -> np.ndarray:
    """vectorized calculation of distance"""

    coords = np.array(
        [
            [star.coords[0], star.coords[1]]
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
