from pathlib import Path
from sys import displayhook

from astromap.star import BrightStar, BrightEdge, BrightGroup, BrightSky
from astromap.catalog import BrightStarCatalog
from astromap.segment import segment
import numpy as np


vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)


log_path = Path(__file__).parent / ".." / "build" / "exercise_catalog_log.txt"

with open(log_path, "w") as log_file:
    sky: BrightSky | None = None
    star_count: int = 1000
    magnitude_offset: float = 1.5
    magnitude_power: float = 0.5
    initial_distance_power: float = 1.5
    initial_distance_coefficient: float = 1.0
    initial_lonely_ratio: float = 0.0
    for magnitude_power_step in range(10):
        magnitude_power += 0.1
        distance_power = initial_distance_power
        for distance_power_step in range(10):
            distance_power += 0.1
            distance_coefficient = initial_distance_coefficient
            for distance_coefficient_step in range(15):
                distance_coefficient += distance_coefficient_step
                lonely_ratio = initial_lonely_ratio
                for lonely_ratio_step in range(5):
                    lonely_ratio += 0.1

                    stars: list[BrightStar] = [
                        catalog.bright(i) for i in range(star_count)
                    ]
                    sky = segment(
                        stars,
                        magnitude_offset=magnitude_offset,
                        magnitude_power=magnitude_power,
                        distance_power=distance_power,
                        distance_coefficient=distance_coefficient,
                        lonely_ratio=lonely_ratio,
                    )

                    # for draft in sky.drafts:
                    # print(draft)

                    stats = []
                    max_stars = 0
                    for group in sky.groups.values():
                        stats.append([group.number, len(group.stars)])
                        max_stars = max(max_stars, len(group.stars))

                    print(
                        f"\n{star_count}, {magnitude_offset}, "
                        f"{magnitude_power}, {distance_power}, "
                        f"{distance_coefficient}, {lonely_ratio}"
                        f"\n\tnumber: {len(stats)}"
                        f"\n\tmax: {max_stars}"
                        f"\n\tgroups: {stats}",
                        file=log_file,
                    )

                    print(
                        f"\n{star_count}, {magnitude_offset}, "
                        f"{magnitude_power}, {distance_power}, "
                        f"{distance_coefficient}, {lonely_ratio}"
                        f"\n\tnumber: {len(stats)}"
                        f"\n\tmax: {max_stars}"
                        f"\n\tgroups: {stats}"
                    )
