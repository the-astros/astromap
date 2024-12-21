from pathlib import Path

from astromap.catalog import BrightStarCatalog
from astromap.starmap import StarMap


vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

image_build_path = Path(__file__).parent / ".." / "build"

try:
    image_build_path.mkdir()
except FileExistsError:
    pass

image_path = str((image_build_path / "map.png").resolve())

stars = [catalog.bright(i) for i in range(500)]

starmap = StarMap(stars, size=10)
starmap.render_png(image_path)

