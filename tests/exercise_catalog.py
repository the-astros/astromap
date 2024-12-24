from pathlib import Path

from astromap.catalog import BrightStarCatalog
from astromap.segment import SkySegmenter

vendor_dir_path = Path(__file__).parent / ".." / "vendor" / "ybsc5" / "catalog"
table = open(vendor_dir_path)
catalog = BrightStarCatalog(table)

segmenter = SkySegmenter(catalog)
