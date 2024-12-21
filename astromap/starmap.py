import math

import cairo

from astromap.star import BrightStar


class StarMap:
    def __init__(
        self, stars: list[BrightStar], size: int = 9, pad: int = 16
    ) -> None:
        self._stars: list[BrightStar] = list(stars)

        # size of rendered image in pixels
        self._map_px_size: int = 2**size
        self._map_px_pad: int = math.floor(self._map_px_size / pad)
        self._px_width: int = (self._map_px_size * 2) + (self._map_px_pad * 2)
        self._px_height: int = self._map_px_size + (self._map_px_pad * 2)

        # amount to scale rendering in cairo to fill image
        self._map_scale: float = self._map_px_size / math.pi

        # set size of stars
        self._star_base: float = 6.0
        self._star_k: float = 0.005

        self._field_color: tuple[float, float, float, float] = (
            0.1,
            0.0,
            0.2,
            1.0,
        )
        self._star_color: tuple[float, float, float, float] = (
            1.0,
            1.0,
            0.8,
            1.0,
        )
        self._star_stroke: float = 0.008

    def render_map(self, context: cairo.Context) -> None:
        # set padded & scaled origin
        context.translate(self._map_px_pad, self._map_px_pad)
        context.scale(self._map_scale, self._map_scale)

        # draw field
        context.set_source_rgba(*self._field_color)
        context.rectangle(0, 0, math.pi * 2, math.pi)
        context.fill()

        context.set_source_rgba(*self._star_color)
        context.set_line_width(self._star_stroke)

        for star in self._stars:
            # push context & translate to center of star
            context.save()
            context.translate(
                (math.pi * 2) - star.coords.azimuth, star.coords.zenith
            )

            self.render_star(context, star.magnitude)

            # pop context
            context.restore()

    def render_star(self, context: cairo.Context, magnitude: float):
        radius: float = (
            max(1, (self._star_base - magnitude) ** 1.3)
        ) * self._star_k

        # Draw the circle
        context.arc(0, 0, radius, 0, 2 * math.pi)
        context.stroke()

    def render_png(self, path: str) -> None:
        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, self._px_width, self._px_height
        )
        context = cairo.Context(surface)

        self.render_map(context)

        print(f"writing image to '{path}'")

        surface.write_to_png(path)
