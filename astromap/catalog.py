from pathlib import Path
from typing import TextIO

from astromap.star import BrightStar, star_from_catalog


class BrightStarCatalog:
    """
    catalog of bright stars from the yale bright star catalog
    """

    def __init__(self, table: TextIO) -> None:
        self._stars: dict[int, BrightStar] = {}

        for row in table:
            star = star_from_catalog(row)
            if star is not None:
                self._stars[star.number] = star

