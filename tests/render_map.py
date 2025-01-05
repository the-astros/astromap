from pathlib import Path

from astromap.catalog import BrightStarCatalog
from astromap.segment import SkySegmenter, BrightEdge as SegmenterEdge
from astromap.star import BrightStar, BrightEdge, BrightGroup
from astromap.starmap import BrightStarMap


vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

segmenter = SkySegmenter(catalog)
segmenter.segment(max_magnitude=4.0)

image_build_path = Path(__file__).parent / ".." / "build"

try:
    image_build_path.mkdir()
except FileExistsError:
    pass

image_path = str((image_build_path / "map.png").resolve())

stars, edges, groups = segmenter.get_stars()

starmap = BrightStarMap(stars, edges, groups, size=10)
starmap.render_png(image_path)

