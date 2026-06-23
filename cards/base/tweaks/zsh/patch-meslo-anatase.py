#!/usr/bin/fontforge -script

import sys

import fontforge
import psMat


ANATASE_CODEPOINT = 0x10A7A5
ANATASE_GLYPH_NAME = "u10A7A5"


def _usage() -> None:
    print(
        "usage: patch-meslo-anatase.py <input.ttf> <logo.svg> <output.ttf>",
        file=sys.stderr,
    )


def _scale_and_center(glyph, font) -> None:
    xmin, ymin, xmax, ymax = glyph.boundingBox()
    width = xmax - xmin
    height = ymax - ymin
    if width <= 0 or height <= 0:
        raise RuntimeError("imported Anatase glyph has an empty outline")

    try:
        advance = font[ord(" ")].width
    except (KeyError, TypeError):
        advance = font.em
    target_width = advance * 1.20
    target_height = (font.ascent + font.descent) * 0.92
    scale = min(target_width / width, target_height / height)
    glyph.transform(psMat.scale(scale))

    xmin, ymin, xmax, ymax = glyph.boundingBox()
    center_x = (xmin + xmax) / 2
    center_y = (ymin + ymax) / 2
    target_center_x = advance / 2
    target_center_y = (font.ascent - font.descent) / 2
    glyph.transform(psMat.translate(target_center_x - center_x, target_center_y - center_y))
    glyph.width = int(advance)


def main() -> int:
    if len(sys.argv) != 4:
        _usage()
        return 2

    input_font, logo_svg, output_font = sys.argv[1:]
    font = fontforge.open(input_font)
    glyph = font.createChar(ANATASE_CODEPOINT, ANATASE_GLYPH_NAME)
    glyph.clear()
    glyph.importOutlines(logo_svg)
    glyph.correctDirection()
    glyph.removeOverlap()
    glyph.simplify()
    _scale_and_center(glyph, font)
    font.generate(output_font)
    font.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
