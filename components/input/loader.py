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

"""Validate structured pinout input and resolve categories before rendering."""

from dataclasses import dataclass
from importlib.resources import files
import json
from math import isfinite
from pathlib import Path

from jsonschema import Draft202012Validator

from components.renderer import (
    BottomLeftCommentsRenderer, CommentsRenderer,
    LegendEntry, LegendRenderer, Orientation, PinDefinition, PinLabel,
    PinType,
    SvgDocument, TopLeftPackageRenderer, TopRightLegendRenderer,
)
from components.renderer.packages.registry import get_package


_DEFAULT_COLORS = {
    "ground": "#202020", "power": "#E53935", "control": "#FDD835",
    "io": "#FFF59D", "analog": "#66BB6A", "pwm": "#EF9A9A",
    "spi": "#26C6DA", "i2c": "#26C6DA", "serial": "#26C6DA",
    "alternate": "#E0E0E0", "board": "#A67C52", "nc": "#FFFFFF",
}


@dataclass(frozen=True)
class PinoutInput:
    """Validated function definitions and separate electrical roles for every pin.

    Function columns count outward after the required pin-type badge. Definitions
    and pin types are immutable tuples ordered by physical pin number.
    legend_columns is optional; None retains automatic legend layout.
    """

    name: str
    pin_count: int
    orientation: Orientation
    content_scale: float
    definitions: tuple[tuple[int, tuple[PinDefinition, ...]], ...]
    pin_types: tuple[tuple[int, PinType], ...]
    legend: tuple[LegendEntry, ...] = ()
    comments: tuple[str, ...] = ()
    family: str = "DIP"
    legend_columns: int | None = None

    def render(
        self, *, legend_renderer: LegendRenderer | None = None,
        comments_renderer: CommentsRenderer | None = None,
    ) -> SvgDocument:
        """Draw the pinout, nominal package measurements, legend, and comments."""
        plugin = get_package(self.family)
        package = plugin.create_renderer(self.pin_count)
        document = plugin.pinout_factory(package).render(
            self.name, dict(self.definitions), self.orientation,
            content_scale=self.content_scale,
            pin_types=dict(self.pin_types),
        )
        package_bounds = TopLeftPackageRenderer().render(document, package)
        renderer = (
            TopRightLegendRenderer(
                reserved_bounds=package_bounds, columns=self.legend_columns
            )
            if legend_renderer is None else legend_renderer
        )
        if self.legend:
            renderer.render(document, self.legend)
        if self.comments:
            comments_style = (
                BottomLeftCommentsRenderer()
                if comments_renderer is None else comments_renderer
            )
            comments_style.render(document, self.comments)
        return document


def _text_color(background: str) -> str:
    red, green, blue = (int(background[i:i + 2], 16) for i in (1, 3, 5))
    brightness = (299 * red + 587 * green + 114 * blue) / 1000
    return "#FFFFFF" if brightness < 140 else "#202020"


def parse_input(data: object) -> PinoutInput:
    """Validate JSON structure, cross references, pin completeness, and columns.

    Raises:
        ValueError: Input is invalid; the message identifies the offending field.
    """
    schema = json.loads(files("components.input").joinpath("schema.json")
                        .read_text(encoding="utf-8"))
    error = next(Draft202012Validator(schema).iter_errors(data), None)
    if error is not None:
        path = ".".join(str(part) for part in error.absolute_path) or "input"
        raise ValueError(f"{path}: {error.message}")

    # Schema validation establishes the structure; these rules compare fields.
    count = data["package"]["pin_count"]
    if type(count) is not int:
        raise ValueError("package.pin_count must be an integer.")
    family = data["package"]["family"]
    get_package(family).create_renderer(count)
    legend_columns = data.get("legend_columns")
    if legend_columns is not None and type(legend_columns) is not int:
        raise ValueError("legend_columns must be an integer or null.")
    content_scale = data.get("content_scale", 0.6)
    if not isfinite(content_scale):
        raise ValueError("content_scale must be finite.")
    seen = set()
    definitions = []
    pin_types = []
    categories = data["categories"]
    category_labels: dict[str, list[PinLabel]] = {}
    for pin in data["pins"]:
        number = pin["number"]
        if type(number) is not int or number not in range(1, count + 1):
            raise ValueError(f"Pin {number}: number must be an integer in 1..{count}.")
        if number in seen:
            raise ValueError(f"Pin {number}: duplicate physical pin number.")
        seen.add(number)
        pin_types.append((number, PinType(pin["type"])))
        columns = set()
        labels = []
        for definition in pin["definitions"]:
            column = definition["column"]
            category = definition["category"]
            if type(column) is not int or column in columns:
                raise ValueError(f"Pin {number}: invalid or duplicate column {column}.")
            if category not in categories:
                raise ValueError(f"Pin {number}: unknown category {category!r}.")
            columns.add(column)
            style = categories[category]
            color = definition.get(
                "color", style.get("color", _DEFAULT_COLORS.get(category, "#E0E0E0"))
            )
            foreground = definition.get(
                "text_color", style.get("text_color", _text_color(color))
            )
            label = PinLabel(
                definition["name"], color, foreground
            )
            labels.append(PinDefinition(column, label))
            category_labels.setdefault(category, []).append(label)
        ordered_labels = tuple(sorted(labels, key=lambda item: item.column))
        definitions.append((number, ordered_labels))
    missing = sorted(set(range(1, count + 1)) - seen)
    if missing:
        raise ValueError(f"Missing physical pins: {missing}.")

    legend = []
    for category in sorted(category_labels, key=lambda item: (item != "power", item)):
        by_color: dict[tuple[str, str], PinLabel] = {}
        for label in sorted(category_labels[category], key=lambda item: item.text):
            key = (label.color.lower(), label.text_color.lower())
            by_color.setdefault(key, label)
        base_color = categories[category].get(
            "color", _DEFAULT_COLORS.get(category, "#E0E0E0")
        ).lower()
        keys = sorted(by_color, key=lambda key: (key[0] != base_color, key))
        samples = tuple(by_color[key] for key in keys)
        legend.append(
            LegendEntry(samples[0], categories[category]["name"], samples[1:])
        )

    return PinoutInput(
        name=data["name"],
        pin_count=count,
        orientation=Orientation[data.get("orientation", "landscape").upper()],
        content_scale=content_scale,
        definitions=tuple(sorted(definitions)),
        pin_types=tuple(sorted(pin_types)),
        legend=tuple(legend),
        comments=tuple(data.get("comments", [])),
        family=family,
        legend_columns=legend_columns,
    )


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}.")
        result[key] = value
    return result


def load_input(path: str | Path) -> PinoutInput:
    """Read and validate a UTF-8 JSON file, rejecting duplicate object keys."""
    with Path(path).open(encoding="utf-8") as source:
        return parse_input(json.load(source, object_pairs_hook=_unique_keys))
