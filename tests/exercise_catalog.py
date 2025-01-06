from pathlib import Path

from astromap.star import BrightStar, BrightEdge, BrightGroup, BrightSky
from astromap.catalog import BrightStarCatalog
from astromap.segment import segment
import numpy as np


vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

stars: list[BrightStar] = [catalog.bright(i) for i in range(100)]

sky = segment(stars)

for draft in sky.drafts:
  print(draft)
  
for i, group in sky.groups.items():
  print(f"{i}: {group}")

print(f"groups: {sky.groups.keys()}")
