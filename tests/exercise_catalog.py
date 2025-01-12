from pathlib import Path
from sys import displayhook
import numpy as np
import math

from astromap.star import BrightStar, BrightEdge, BrightGroup, BrightSky
from astromap.catalog import BrightStarCatalog
from astromap.segment import segment

vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

(
    star_count,
    magnitude_offset,
    magnitude_power,
    distance_power,
    distance_coefficient,
    rival_coefficient,
    lonely_ratio,
) = [100, 1.5, 1.0, 2.0, 256.0, 4096.0, 0.2]

stars: list[BrightStar] = [
    catalog.bright(i) for i in range(star_count)
]
sky = segment(
    stars,
    magnitude_offset=magnitude_offset,
    magnitude_power=magnitude_power,
    distance_power=distance_power,
    distance_coefficient=distance_coefficient,
    rival_coefficient=rival_coefficient,
    lonely_ratio=lonely_ratio,
)
