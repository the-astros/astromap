from pathlib import Path
import numpy as np

from astromap.catalog import BrightStarCatalog
from astromap.segment import segment
from astromap.star import BrightSky, BrightStar, BrightEdge, BrightGroup
from astromap.starmap import BrightStarMap

image_build_path = Path(__file__).parent / ".." / "build" / "search"


def render(sky: BrightSky, image_path: str):
    try:
        image_build_path.mkdir()
    except FileExistsError:
        pass

    starmap = BrightStarMap(sky, size=10)
    starmap.render_png(image_path)


(
    star_count,
    magnitude_offset,
    magnitude_power_base,
    distance_power_base,
    distance_coefficient_base,
    rival_coefficient_base,
) = [330, 1.5, 0.5, 1.5, 32.0, 18]

max_score = 0
max_group = None
max_groups = []

for mag_step, dis_pow_step, dis_co_step, rival_step in np.ndindex(
    10, 10, 32, 36
):
    magnitude_power = magnitude_power_base + (mag_step * 0.1)
    distance_power = distance_power_base + (dis_pow_step * 0.1)
    distance_coefficient = distance_coefficient_base + (dis_co_step * 32.0)
    rival_coefficient = 1.5 ** (rival_coefficient_base + rival_step)

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
    )

    five_plus = 0
    max_stars = 2
    groups = []
    for number, group in sky.groups.items():
        groups.append((number, len(group.stars)))

    max_draft = sky.drafts[sky.max_draft]
    group_data = (
        sky.score,
        max_draft.pick,
        max_draft.five_plus,
        max_draft.ten_plus,
        max_draft.max_count,
        (
            star_count,
            magnitude_offset,
            magnitude_power,
            distance_power,
            distance_coefficient,
            rival_coefficient,
        ),
        groups,
    )

    if sky.score > max_score:
        max_score = sky.score
        max_group = group_data
        print("\n***new max score***")

    if sky.score >= 30 and sky.score >= max_score - 5:
        print(f"\n*new groups: {groups}")

        max_groups.append(group_data)

        image_path = str(
            (
                image_build_path / f"map-rivalv0.4.0-{sky.score}"
                f"--{star_count}-{magnitude_offset:.1f}"
                f"-{magnitude_power:.1f}-{distance_power:.1f}"
                f"-{distance_coefficient:.1f}-{rival_coefficient:.1f}.png"
            ).resolve()
        )
        render(sky, image_path)

print("\nmax groups:")
for i, group in enumerate(max_groups):
    print(f"\n{i}: {group}")

print(f"maxxest group: {max_group}")
