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


log_path = Path(__file__).parent / ".." / "build" / "exercise_catalog_log.txt"

with open(log_path, "w") as log_file:
    sky: BrightSky | None = None
    star_count: int = 2000
    magnitude_offset: float = 1.5
    magnitude_power: float = 1.0
    initial_distance_power: float = 1.7
    initial_distance_coefficient: float = 56.0
    # initial_lonely_ratio: float = 0.0
    lonely_ratio: float = 0.2
    max_group = {
        "ten_plus": 0,
        "median": 0,
        "star_count": 1000,
        "magnitude_offset": 1.5,
        "magnitude_power": 0.5,
        "distance_power": 1.5,
        "distance_coefficient": 16.0,
        "lonely_ratio": 0.4,
    }
    # for magnitude_power_step in range(3):
    #     magnitude_power += 0.1
    distance_power = initial_distance_power
    for distance_power_step in range(4):
        distance_power += 0.1
        distance_coefficient = initial_distance_coefficient
        for distance_coefficient_step in range(6):
            distance_coefficient += 8.0
            # lonely_ratio = initial_lonely_ratio
            # for lonely_ratio_step in range(5):
            #     lonely_ratio += 0.1

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
            counts = []
            max_stars = 0
            three_plus = 0
            five_plus = 0
            ten_plus = 0
            twenty_plus = 0
            for group in sky.groups.values():
                stats.append([group.number, len(group.stars)])
                counts.append(len(group.stars))
                max_stars = max(max_stars, len(group.stars))
                if len(group.stars) > 2:
                    three_plus += 1
                if len(group.stars) > 4:
                    five_plus += 1
                if len(group.stars) > 9:
                    ten_plus += 1
                if len(group.stars) > 19:
                    twenty_plus += 1
            median_index = math.floor(len(counts) / 2)
            median = counts[median_index] if len(counts) > median_index else 0

            if ten_plus > max_group["ten_plus"]:
                max_group["ten_plus"] = ten_plus
                max_group["median"] = median
                max_group["star_count"] = star_count
                max_group["magnitude_offset"] = magnitude_offset
                max_group["magnitude_power"] = magnitude_power
                max_group["distance_power"] = distance_power
                max_group["distance_coefficient"] = distance_coefficient
                max_group["lonely_ratio"] = lonely_ratio

                print(f"new max group: {max_group}")
                print(f"new max group: {max_group}", file=log_file)

            if ten_plus > 5:
                print(
                    f"\n{star_count}, {magnitude_offset}, "
                    f"{magnitude_power}, {distance_power}, "
                    f"{distance_coefficient}, {lonely_ratio}"
                    f"\n\tnumber: {len(stats)}"
                    f" 3+: {three_plus}"
                    f" 5+: {five_plus}"
                    f" 10+: {ten_plus}"
                    f" 20+: {twenty_plus}"
                    f"\n\tmedian: {median}"
                    f"\n\tmax: {max_stars}"
                    f"\n\tgroups: {stats}"
                )

            if ten_plus > 7:
                print(
                    f"\n{star_count}, {magnitude_offset}, "
                    f"{magnitude_power}, {distance_power}, "
                    f"{distance_coefficient}, {lonely_ratio}"
                    f"\n\tnumber: {len(stats)}"
                    f" 3+: {three_plus}"
                    f" 5+: {five_plus}"
                    f" 10+: {ten_plus}"
                    f" 20+: {twenty_plus}"
                    f"\n\tmedian: {median}"
                    f"\n\tmax: {max_stars}"
                    f"\n\tgroups: {stats}",
                    file=log_file,
                )

    print(f"max group: {max_group}")

    print(f"max group: {max_group}", file=log_file)
