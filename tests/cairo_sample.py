import os
from typing import Callable

import cairo

type Drawer = Callable[[cairo.Context, int, int], str]


def render_png(drawer: Drawer):
    width, height = 256, 256

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)

    cr.save()
    name = drawer(cr, width, height)

    cr.restore()

    try:
        os.makedirs(os.path.join("build"))
    except EnvironmentError:
        pass
    filename = os.path.join("build", f"{name}.png")

    print(f"writing image to '{filename}'")

    surface.write_to_png(filename)


def drawer(context: cairo.Context, width: int, height: int) -> str:
    x, y, x1, y1 = 0.1, 0.5, 0.4, 0.9
    x2, y2, x3, y3 = 0.6, 0.1, 0.9, 0.5
    context.scale(200, 200)
    context.set_line_width(0.04)
    context.move_to(x, y)
    context.curve_to(x1, y1, x2, y2, x3, y3)
    context.stroke()
    context.set_source_rgba(1, 0.2, 0.2, 0.6)
    context.set_line_width(0.02)
    context.move_to(x, y)
    context.line_to(x1, y1)
    context.move_to(x2, y2)
    context.line_to(x3, y3)
    context.stroke()

    return "sample"


if __name__ == "__main__":
    if not (cairo.HAS_IMAGE_SURFACE and cairo.HAS_PNG_FUNCTIONS):
        raise SystemExit(
            "cairo was not compiled with ImageSurface and PNG support"
        )

    render_png(drawer)
