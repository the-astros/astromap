from pathlib import Path

from astromap.catalog import BrightStarCatalog
from astromap.segment import segment
from astromap.star import BrightStar, BrightEdge, BrightGroup
from astromap.starmap import BrightStarMap


(
    star_count,
    magnitude_offset,
    magnitude_power,
    distance_power,
    distance_coefficient,
    lonely_ratio,
) = [1000, 1.5, 1.0, 2.0, 4.0, 0.5]
# ) = [1000, 1.5, 0.6, 1.6, 16.0, 0.5]
# ) = [1000, 1.5, 1.0, 1.8, 46.0, 0.3]

vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

stars = [catalog.bright(i) for i in range(star_count)]

sky = segment(
    stars,
    magnitude_offset=magnitude_offset,
    magnitude_power=magnitude_power,
    distance_power=distance_power,
    distance_coefficient=distance_coefficient,
    lonely_ratio=lonely_ratio,
)

image_build_path = Path(__file__).parent / ".." / "build"

try:
    image_build_path.mkdir()
except FileExistsError:
    pass

image_path = str(
    (
        image_build_path
        / f"map-{star_count}-{magnitude_offset}-{magnitude_power}"
        f"-{distance_power}-{distance_coefficient}-{lonely_ratio}.png"
    ).resolve()
)


starmap = BrightStarMap(sky, size=10)
starmap.render_png(image_path)
