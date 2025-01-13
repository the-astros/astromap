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
    rival_coefficient,
) = [330, 1.5, 1.0, 2.0, 64.0, 287626.5]
# ) = [330, 1.5, 1.0, 2.0, 64.0, 25251.2, 0.03]
# ) = [330, 1.5, 1.0, 2.0, 64.0, 25251.2, 0.02]
# ) = [330, 1.5, 1.0, 2.0, 64.0, 2048, 0.03]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 18, 0.1]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 16, 0.15]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 17, 0.1]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 16, 0.1]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 15, 0.1]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2.0 ** 14, 0.1]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 4.0, 0.2]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2048.0, 0.3]
# ) = [300, 1.5, 1.0, 2.0, 256.0, 2048.0, 0.1]


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
    rival_coefficient=rival_coefficient,
)

image_build_path = Path(__file__).parent / ".." / "build"

try:
    image_build_path.mkdir()
except FileExistsError:
    pass

image_path = str(
    (
        image_build_path
        / f"map-rivalv0.4.0-{star_count}-{magnitude_offset}-{magnitude_power}"
        f"-{distance_power}-{distance_coefficient}-{rival_coefficient}.png"
    ).resolve()
)


starmap = BrightStarMap(sky, size=10)
starmap.render_png(image_path)
