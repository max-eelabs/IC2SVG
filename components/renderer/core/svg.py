# Copyright 2026 Maxim Pavlov <pavlov.web@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""SVG drawing primitives and font outlines with no embedded raster content."""

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from io import BytesIO
from math import isfinite
from pathlib import Path
from xml.etree import ElementTree as ET

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import ImageFont


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


@lru_cache(maxsize=1)
def _outline_font() -> TTFont:
    # Use exactly the same embedded font as the original Pillow renderer.
    font = ImageFont.load_default(size=36)
    return TTFont(BytesIO(font.font_bytes))


class SvgDocument:
    """Own a vector drawing in fixed logical units and serialize it as SVG.

    Drawing calls mutate this document. Saving writes UTF-8 SVG to the requested
    path; scaling changes only the viewport, preserving all geometry and strokes.
    """

    def __init__(
        self, size: tuple[int, int], *, content_scale: float = 1.0
    ) -> None:
        """Create a white sheet with uniformly scaled content about its center.

        Content scale is in (0, 1]; viewport export scaling remains independent.
        Drawing coordinates and text measurements remain in logical units.
        """
        if not isfinite(content_scale) or not 0 < content_scale <= 1:
            raise ValueError("Content scale must be finite and in (0, 1].")
        self.size = size
        self.content_scale = content_scale
        self._fill_overrides: dict[str, str] = {}
        self._split_fills: dict[str, tuple[tuple[str, ...], tuple[float, ...]]] = {}
        self._clip_count = 0
        self._root = ET.Element(
            "svg",
            {
                "xmlns": "http://www.w3.org/2000/svg",
                "viewBox": f"0 0 {size[0]} {size[1]}",
            },
        )
        self._drawing_root = self._root
        self._add("rect", x=0, y=0, width=size[0], height=size[1], fill="white")
        if content_scale != 1:
            offset_x = size[0] * (1 - content_scale) / 2
            offset_y = size[1] * (1 - content_scale) / 2
            transform = (
                f"translate({_number(offset_x)} {_number(offset_y)}) "
                f"scale({_number(content_scale)})"
            )
            self._drawing_root = ET.SubElement(self._root, "g", {
                "id": "drawing", "transform": transform,
            })

    def _add(self, tag: str, **attributes: str | float) -> ET.Element:
        fill = attributes.get("fill")
        if isinstance(fill, str) and fill in self._fill_overrides:
            attributes["fill"] = self._fill_overrides[fill]
        values = {
            key.replace("_", "-"): value if isinstance(value, str) else _number(value)
            for key, value in attributes.items()
        }
        if values.get("fill") in self._split_fills:
            return self._add_split_shape(tag, values)
        return ET.SubElement(self._drawing_root, tag, values)

    def _add_split_shape(self, tag: str, values: dict[str, str]) -> ET.Element:
        colors, bounds = self._split_fills[values["fill"]]
        left, top, right, bottom = bounds
        self._clip_count += 1
        identifier = f"split-clip-{self._clip_count}"
        definitions = ET.Element("defs")
        self._root.insert(0, definitions)
        clip = ET.SubElement(definitions, "clipPath", {"id": identifier})
        geometry = {
            key: value for key, value in values.items()
            if key not in ("fill", "stroke", "stroke-width")
        }
        ET.SubElement(clip, tag, geometry)
        bands = ET.SubElement(self._drawing_root, "g", {
            "clip-path": f"url(#{identifier})",
        })
        for index, color in enumerate(colors):
            x1 = left + (right - left) * index / len(colors)
            x2 = left + (right - left) * (index + 1) / len(colors)
            ET.SubElement(bands, "path", {
                "d": f"M {x1} {top} H {x2} V {bottom} H {x1} Z", "fill": color,
            })
        # One outer outline encloses all bands; there is no border between colors.
        values["fill"] = "none"
        return ET.SubElement(self._drawing_root, tag, values)

    def split_fill(
        self, colors: tuple[str, ...], bounds: tuple[float, float, float, float]
    ) -> str:
        """Create equal hard-stop color bands for one shape's fill, left to right."""
        if not colors:
            raise ValueError("Split fill needs at least one color.")
        reference = f"url(#split-fill-{len(self._split_fills) + 1})"
        self._split_fills[reference] = (colors, bounds)
        return reference

    @contextmanager
    def override_fill(
        self, source: str, replacement: str
    ) -> Generator[None, None, None]:
        """Temporarily substitute a fill without changing the drawing strategy."""
        previous = self._fill_overrides.copy()
        self._fill_overrides[source] = replacement
        try:
            yield
        finally:
            self._fill_overrides = previous

    @contextmanager
    def sheet_layer(
        self, name: str, *, position: tuple[float, float] = (0, 0),
        scale: float = 1.0,
    ) -> Generator[None, None, None]:
        """Draw an overlay in sheet coordinates, independent of content scaling.

        Restore the previous drawing target even if the overlay renderer fails.
        """
        if not isfinite(scale) or scale <= 0:
            raise ValueError("Sheet layer scale must be finite and positive.")
        previous = self._drawing_root
        transform = (
            f"translate({_number(position[0])} {_number(position[1])}) "
            f"scale({_number(scale)})"
        )
        self._drawing_root = ET.SubElement(
            self._root, "g", {"id": name, "transform": transform}
        )
        try:
            yield
        finally:
            self._drawing_root = previous

    def rounded_rectangle(
        self,
        box: tuple[float, float, float, float],
        *,
        radius: float,
        fill: str,
        outline: str,
        width: float,
    ) -> None:
        """Draw a rounded rectangle with a centered vector stroke."""
        left, top, right, bottom = box
        self._add(
            "rect", x=left, y=top, width=right - left, height=bottom - top,
            rx=radius, fill=fill, stroke=outline, stroke_width=width,
        )

    def polygon(
        self,
        points: list[tuple[float, float]],
        *,
        fill: str,
        outline: str,
        width: float,
    ) -> None:
        """Draw a closed polygon."""
        self._add(
            "polygon",
            points=" ".join(f"{_number(x)},{_number(y)}" for x, y in points),
            fill=fill, stroke=outline, stroke_width=width,
        )

    def line(
        self,
        coordinates: tuple[float, float, float, float],
        *,
        fill: str,
        width: float,
    ) -> None:
        """Draw a line with a scalable stroke."""
        x1, y1, x2, y2 = coordinates
        self._add(
            "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=fill, stroke_width=width
        )

    def path(self, data: str, *, fill: str, outline: str, width: float) -> None:
        """Draw an SVG path expressed in logical canvas units."""
        self._add("path", d=data, fill=fill, stroke=outline, stroke_width=width)

    def ellipse(
        self,
        box: tuple[float, float, float, float],
        *,
        fill: str,
        outline: str,
        width: float,
    ) -> None:
        """Draw an ellipse inside the supplied bounds."""
        left, top, right, bottom = box
        self._add(
            "ellipse", cx=(left + right) / 2, cy=(top + bottom) / 2,
            rx=(right - left) / 2, ry=(bottom - top) / 2,
            fill=fill, stroke=outline, stroke_width=width,
        )

    def text(
        self,
        position: tuple[float, float],
        text: str,
        *,
        font: ImageFont.FreeTypeFont,
        fill: str,
        anchor: str,
        bold: bool = False,
    ) -> None:
        """Draw font outlines with optional deterministic outline emboldening.

        Raises:
            ValueError: A character has no outline in the fixed embedded font.
        """
        outline_font = _outline_font()
        glyphs = outline_font.getGlyphSet()
        cmap = outline_font.getBestCmap()
        scale = font.size / outline_font["head"].unitsPerEm
        x, y = position
        advance = font.getlength(text)
        if anchor == "mm":
            x -= advance / 2
        elif anchor == "rm":
            x -= advance

        # Reproduce Pillow's ascender/descender-based vertical middle anchor.
        ascent, descent = font.getmetrics()
        y += (ascent - descent) / 2
        group = self._add("g", fill=fill, aria_label=text)
        if bold:
            # Glyph paths use font units; their transforms scale this stroke with
            # both the font size and the containing SVG drawing.
            group.set("stroke", fill)
            group.set("stroke-width", _number(outline_font["head"].unitsPerEm * 0.025))
            group.set("stroke-linejoin", "round")
            group.set("paint-order", "stroke fill")

        for index, character in enumerate(text):
            glyph_name = cmap.get(ord(character))
            if glyph_name is None:
                raise ValueError(f"Unsupported character in IC label: {character!r}")
            pen = SVGPathPen(glyphs)
            glyphs[glyph_name].draw(pen)
            offset = font.getlength(text[:index + 1]) - font.getlength(character)
            transform = (
                f"translate({_number(x + offset)} {_number(y)}) "
                f"scale({_number(scale)} {_number(-scale)})"
            )
            ET.SubElement(
                group, "path", {"d": pen.getCommands(), "transform": transform}
            )

    @staticmethod
    def text_bounds(
        position: tuple[float, float], text: str, *,
        font: ImageFont.FreeTypeFont, anchor: str,
        bold: bool = False,
    ) -> tuple[float, float, float, float]:
        """Measure the visible vector outlines using the same anchors as text()."""
        outline_font = _outline_font()
        glyphs = outline_font.getGlyphSet()
        cmap = outline_font.getBestCmap()
        scale = font.size / outline_font["head"].unitsPerEm
        x, y = position
        if anchor == "mm":
            x -= font.getlength(text) / 2
        elif anchor == "rm":
            x -= font.getlength(text)
        ascent, descent = font.getmetrics()
        y += (ascent - descent) / 2
        boxes = []

        for index, character in enumerate(text):
            glyph_name = cmap.get(ord(character))
            if glyph_name is None:
                raise ValueError(f"Unsupported character in IC label: {character!r}")
            pen = BoundsPen(glyphs)
            glyphs[glyph_name].draw(pen)
            if pen.bounds is None:
                continue
            left, bottom, right, top = pen.bounds
            offset = font.getlength(text[:index + 1]) - font.getlength(character)
            boxes.append((x + offset + left * scale, y - top * scale,
                          x + offset + right * scale, y - bottom * scale))

        if not boxes:
            raise ValueError("Label must contain a visible glyph.")
        expansion = font.size * 0.025 / 2 if bold else 0
        return (
            min(box[0] for box in boxes) - expansion,
            min(box[1] for box in boxes) - expansion,
            max(box[2] for box in boxes) + expansion,
            max(box[3] for box in boxes) + expansion,
        )

    def to_string(self, *, scale: float = 1.0) -> str:
        """Serialize SVG; positive scale sets viewport size without changing viewBox."""
        if not isfinite(scale) or scale <= 0:
            raise ValueError("SVG scale must be finite and greater than zero.")

        # Serialize a copy so exporting at another size does not mutate the drawing.
        root = ET.fromstring(ET.tostring(self._root))
        root.set("width", _number(self.size[0] * scale))
        root.set("height", _number(self.size[1] * scale))
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        return ET.tostring(
            root, encoding="utf-8", xml_declaration=True
        ).decode("utf-8")

    def save(self, path: str | Path, *, scale: float = 1.0) -> None:
        """Write UTF-8 SVG with LF newlines and a uniformly scaled viewport."""
        Path(path).write_text(
            self.to_string(scale=scale), encoding="utf-8", newline="\n"
        )
