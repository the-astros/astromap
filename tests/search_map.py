from pathlib import Path
import numpy as np

from astromap.catalog import BrightStarCatalog
from astromap.segment import segment
from astromap.star import BrightSky, BrightStar, BrightEdge, BrightGroup
from astromap.starmap import BrightStarMap


def render(sky: BrightSky):
    image_build_path = Path(__file__).parent / ".." / "build" / "search"

    try:
        image_build_path.mkdir()
    except FileExistsError:
        pass

    image_path = str(
        (
            image_build_path
            / f"map-rivalv0.3.0-{star_count}-{magnitude_offset:.1f}"
            f"-{magnitude_power:.1f}-{distance_power:.1f}"
            f"-{distance_coefficient:.1f}-{rival_coefficient:.1f}"
            f"-{lonely_ratio:.2f}.png"
        ).resolve()
    )

    starmap = BrightStarMap(sky, size=10)
    starmap.render_png(image_path)


(
    star_count,
    magnitude_offset,
    magnitude_power,
    distance_power,
    distance_coefficient_base,
    rival_coefficient_base,
    lonely_ratio_base,
) = [330, 1.5, 1.0, 2.0, 64.0, 18, 0.03]

max_five_plus = 0
max_group = None
max_groups = []

for distance_step, rival_step, lonely_step in np.ndindex(16, 18, 24):
    distance_coefficient = distance_coefficient_base + (distance_step * 64.0)
    rival_coefficient = 1.5 ** (rival_coefficient_base + rival_step)
    lonely_ratio = lonely_ratio_base + (lonely_step * 0.01)

    vendor_dir_path = (
        Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
    )
    table = open(vendor_dir_path)
    catalog = BrightStarCatalog(table)

    stars = [catalog.bright(i) for i in range(star_count)]

    sky = segment(
        stars,
        magnitude_offset=magnitude_offset,
        magnitude_power=magnitude_power,
        distance_power=distance_power,
        distance_coefficient=distance_coefficient,
        rival_coefficient=rival_coefficient,
        lonely_ratio=lonely_ratio,
    )

    five_plus = 0
    max_stars = 2
    groups = []
    for number, group in sky.groups.items():
        groups.append((number, len(group.stars)))
        if len(group.stars) >= 5:
            five_plus += 1
        if len(group.stars) > max_stars:
            max_stars = len(group.stars)

    group_data = (
        five_plus,
        max_stars,
        (
            star_count,
            magnitude_offset,
            magnitude_power,
            distance_power,
            distance_coefficient,
            rival_coefficient,
            lonely_ratio,
        ),
        groups,
    )

    if five_plus > max_five_plus:
        max_five_plus = five_plus
        max_group = group_data
        print(f"\n***five up: five plus: {five_plus} max_stars: {max_stars}")

    if max_stars < star_count / 10 and (
        five_plus >= max_five_plus or five_plus > star_count / 20
    ):
        print(f"\n*new group: five plus: {five_plus} max_stars: {max_stars}")
        print(f"\tgroups: {groups}")

        max_groups.append(group_data)

        render(sky)

print("\nmax_groups:")
for i, group in enumerate(max_groups):
    print(f"\n{i}: {group}")

print(f"maxxest group: {max_group}")
