from pathlib import Path
import sqlite3
import logging

from astromap import bright, segment, sphere

logging.basicConfig(level=logging.DEBUG)

db_path: Path = Path(__file__).parent / ".." / "build" / "sphere.db"
catalog_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"

conn: sqlite3.Connection = sqlite3.connect(db_path)

sphere.create_tables(conn)
stars: list[bright.Star] = sphere.select_all_stars(conn)
if len(stars) < 1:
    with open(catalog_path) as table:
        sphere.import_catalog(conn, table)
        stars = sphere.select_all_stars(conn)

print(f"selected {len(stars)} stars")
for i in range(10):
    print(stars[i])

param: segment.Param = segment.Param(
    count=330,
    magnitude_offset=1.5,
    magnitude_power=0.5,
    distance_power=1.6,
    distance_coefficient=2**8,
    rival_power=2.0,
    rival_coefficient=2.0**24,
)

draft, found_new_sky = sphere.draft_skies(conn, param)

skies: list[tuple[float, frozenset[bright.Group]]] = []
raw_skies: dict[int, bright.Sky] = {}
sky_ranks: dict[int, float] = {}
for sky in sphere.select_skies_by_hashes(conn, list(draft.skies)):
    raw_skies[hash(sky)] = sky
    sky_ranks[hash(sky)] = sphere.rank_sky(conn, sky)

for hsh in draft.skies:
    skies.append(
        (
            sky_ranks[hsh],
            frozenset(
                sphere.select_groups_by_hashes(
                    conn, list(raw_skies[hsh].groups)
                )
            ),
        )
    )

max_rank: float = 0.0
max_index: int = 0
for i, (rank, groups) in enumerate(skies):
    is_max: bool = False
    if rank > max_rank:
        is_max = True
        max_rank = rank
        max_index = i
    print(f"{i}: {rank:.2f} -> {"*new max*" if is_max else "-"}")


def print_sky(index: int):
    sky_rank, sky_groups = skies[index]
    print(f"sky draft {index}: rank: {sky_rank:.2f}")
    for group in sky_groups:
        rank = sphere.rank_group(conn, group)
        catalogs = list(group.stars)
        if rank > 0:
            print(f"\trank: {rank} > count: {len(catalogs)} > {catalogs}")

print("*max sky draft*")
print_sky(max_index)
