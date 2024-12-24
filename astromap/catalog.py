from operator import attrgetter
from pathlib import Path
from typing import Iterator, TextIO

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

        self._magnitudes: list[tuple[float, int]] = [
            (star.magnitude, star.number)
            for star in sorted(
                self._stars.values(), key=attrgetter("magnitude")
            )
        ]

    def __getitem__(self, i: int) -> BrightStar:
        return self._stars[i]

    def __iter__(self) -> Iterator[BrightStar]:
        return self._stars.values().__iter__()

    def __len__(self) -> int:
        return len(self._stars)

    def bright(self, n: int) -> BrightStar:
        return self._stars[self._magnitudes[n][1]]
