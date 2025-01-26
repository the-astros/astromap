from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Iterator, TextIO
import json
import logging
import math

import numpy as np
import sqlite3

from astromap import bright, segment


@dataclass
class Draft:
    """
    a draft of skies held with a given set of params
    """

    param_hash: int  # segment param hash is also primary key
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
        stars TEXT
    )
"""
    )

    # create skies table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS skies (
        hsh INTEGER PRIMARY KEY,
        groups TEXT
    )
"""
    )

    # create params table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS params (
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


def select_bright_stars(
    conn: sqlite3.Connection, count: int
) -> list[bright.Star]:
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """
    SELECT catalog, magnitude, coords_0, coords_1, motion_0, motion_1
    FROM stars
    ORDER BY magnitude
    LIMIT ?
""",
        (count,),
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


def select_param_by_hash(
    conn: sqlite3.Connection, hsh: int
) -> segment.Param | None:
    param: segment.Param | None = None
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
        param = segment.Param(row=row)
    return param


def select_draft_by_param_hash(
    conn: sqlite3.Connection, param_hash: int
) -> Draft | None:
    draft: Draft | None = None
    cursor: sqlite3.Cursor = conn.cursor()

    cursor.execute(
        """
    SELECT param_hash, skies
    FROM drafts
    WHERE param_hash = ?
""",
        (param_hash,),
    )
    row = cursor.fetchone()
    if row is not None:
        draft = Draft(
            param_hash=row[0],
            skies=tuple(json.loads(row[3])),
        )
    return draft


def insert_param(
    conn: sqlite3.Connection, param: segment.Param
) -> None:
    """
    insert param into table (if it doesnt exist)
    """
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute(
        """
INSERT OR IGNORE INTO params (
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
        param.row(),
    )

    conn.commit()


def insert_groups(conn: sqlite3.Connection, groups: list[bright.Group]) -> None:
    """
    insert group into table (if it doesnt exist)
    """
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.executemany(
        """
INSERT OR IGNORE INTO group (
    hsh,
    stars
)
VALUES (?, ?)
""",
        [(group.hsh, json.dumps(list(group.stars))) for group in groups],
    )

    conn.commit()


def insert_skies(conn: sqlite3.Connection, skies: list[bright.Sky]) -> None:
    """
    insert group into table (if it doesnt exist)
    """
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.executemany(
        """
INSERT OR IGNORE INTO group (
    hsh,
    stars
)
VALUES (?, ?)
""",
        [(sky.hsh, json.dumps(list(sky.groups))) for sky in skies],
    )

    conn.commit()


def draft_skies(
    conn: sqlite3.Connection, param: segment.Param
) -> tuple[Draft, bool]:
    cursor: sqlite3.Cursor = conn.cursor()

    # check if given params are already drafted
    draft: Draft | None = select_draft_by_param_hash(conn, hash(param))
    found_new_sky: bool = False

    if draft is not None:
        return draft, found_new_sky

    insert_param(conn, param)

    # get list of param.count brightest stars in the sky
    # - ordered from lowest to highest magnitude
    # - lower magnitude is brighter
    stars: list[bright.Star] = select_bright_stars(conn, param.count)

    # print("bright stars:")
    # for i, star in enumerate(stars):
    #     print(f"{i}: {star}")

    # get list of groups and skies visited with given param
    groups, skies = segment.visit(param, stars)

    # insert groups and skies into db
    insert_groups(conn, groups)
    insert_skies(conn, skies)

    # build draft from skies
    draft = Draft(
        param_hash=hash(param),
        skies=tuple([hash(sky) for sky in skies]),
    )

    return draft, found_new_sky
