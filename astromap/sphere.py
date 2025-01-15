from collections.abc import Iterator
from dataclasses import dataclass, field
import json
import math

import sqlite3

@dataclass
class Star:
    """
    parameters of a star from the bright star catalog

    - all coordinates in the j2000 epoch in the fk5 reference frame
    """

    index: int  # bright star catalog index
    magnitude: float  # apparent visual magnitude
    coords: tuple[float, float]  # right ascension, declination
    motion: tuple[float, float]  # proper motion / year


@dataclass
class Group:
    hsh: int  # hash of stars frozenset
    stars: frozenset[int]  # set of bright star catalog numbers
    rating: int  # rating of this group


@dataclass
class Sky:
    hsh: int  # hash of groups frozenset
    groups: frozenset[int]  # set of group hashes
    rating: int  # sum of ratings of groups


@dataclass
class SegmentParameters:
    """
    parameters defining a single segmentation of the sky into groups of stars
    """
    hsh: int  # hash of tuple of other values
    version: str  # semantic version of segmenter
    count: int  # number of stars
    star_count: int
    magnitude_offset: float
    magnitude_power: float
    distance_power: float
    distance_coefficient: float
    rival_power: float
    rival_coefficient: float


@dataclass
class Segment:
    parameters: int  # segment paraters hash is also primary key
    rating: int  # highest rating of drafted skies
    top_draft: int  # draft pick with max rating
    drafts: tuple[int, ...]  # draft list of sky hashes to full merge


class SkySphere:

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._version = "0.5.0"
        self._conn = conn

    def create_tables(self) -> None:
        cursor: sqlite3.Cursor = self._conn.cursor()

        # create stars table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stars (
                index INTEGER PRIMARY KEY,
                magnitude REAL,
                coords_0 REAL,
                coords_1 REAL,
                motion_0 REAL,
                motion_1 REAL,
            )
        ''')

    def import_catalog(self, rows: Iterator[str]) -> None:
        pass

    @staticmethod
    def star_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Star:
        fields = [column[0] for column in cursor.description]
        return Star(**{k: v for k, v in zip(fields, row)})
