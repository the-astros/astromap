from pathlib import Path
import sqlite3

from astromap import sphere

db_path: Path = Path(__file__).parent / ".." / "build" / "sphere.db"
catalog_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"

conn: sqlite3.Connection = sqlite3.connect(db_path)

sphere.create_tables(conn)
stars: list[sphere.Star] = sphere.select_all_stars(conn)
if len(stars) < 1:
    with open(catalog_path) as table:
        sphere.import_catalog(conn, table)
        stars = sphere.select_all_stars(conn)

print(f"selected {len(stars)} stars")
for i in range(10):
    print(stars[i])
