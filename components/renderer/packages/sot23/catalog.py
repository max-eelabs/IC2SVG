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

"""Load package-owned SOT-23 variant assets, with no shared pin-count list.

The schema accepts three, five, and six leads. Measurements in both units are
fixed source text; geometry is illustrative.
Reading these bundled assets has no file-writing or rendering side effects.
"""

from dataclasses import dataclass
from importlib.resources import files
import json
from math import isfinite
from pathlib import Path

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class PackageMeasurement:
    """A fixed source value or range in explicit inch and millimeter text."""

    inches: str
    millimeters: str


@dataclass(frozen=True)
class Sot23Specification:
    """Published body dimensions, free-lead span, pitch, and source for a variant."""

    body_width: PackageMeasurement
    body_length: PackageMeasurement
    lead_span: PackageMeasurement
    pin_pitch: PackageMeasurement
    source: str


@dataclass(frozen=True)
class Sot23Geometry:
    """Top-view body width, length, lead span, lead width, and pitch in mm."""

    width: float
    length: float
    span: float
    shoulder: float
    pitch: float


@dataclass(frozen=True)
class Sot23Variant:
    """Immutable geometry and references with positions in physical-number order.

    Positions are (side, y_offset_mm): -1 means left and +1 means right;
    offsets increase downward from the body center in the rotated top view.
    """

    pin_count: int
    geometry: Sot23Geometry
    specification: Sot23Specification
    pin_positions: tuple[tuple[int, float], ...]


def load_variants(directory: str | Path) -> tuple[Sot23Variant, ...]:
    """Read a SOT-23 variant directory and return records sorted by physical pin count.

    Validates against the bundled variant schema, checks geometry consistency,
    and rejects duplicate counts. Reads UTF-8 JSON without modifying any files.

    Raises:
        ValueError: A variant is invalid, duplicated, or no variant files exist.
        OSError: The directory or an asset cannot be read.
    """
    schema = json.loads(
        files(__package__).joinpath("variant.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    variants: dict[int, Sot23Variant] = {}
    for path in sorted(Path(directory).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        error = next(validator.iter_errors(data), None)
        if error is not None:
            raise ValueError(f"{path.name}: {error.message}")
        count = data["pin_count"]
        if type(count) is not int:
            raise ValueError(f"{path.name}: pin_count must be an integer.")
        if count in variants:
            raise ValueError(f"{path.name}: duplicate SOT-23 pin count {count}.")
        geometry = Sot23Geometry(**data["geometry_mm"])
        if any(not isfinite(value) for value in data["geometry_mm"].values()):
            raise ValueError(f"{path.name}: geometry must be finite.")
        if geometry.span <= geometry.width or geometry.shoulder >= geometry.pitch:
            raise ValueError(
                f"{path.name}: span must exceed width and lead width must be "
                "smaller than pitch."
            )
        positions = tuple(tuple(position) for position in data["pin_positions"])
        if len(positions) != count or len(set(positions)) != count:
            raise ValueError(f"{path.name}: provide one unique position per pin.")
        if any(
            type(side) is not int or not isfinite(offset)
            or abs(offset) + geometry.shoulder / 2 >= geometry.length / 2
            for side, offset in positions
        ):
            raise ValueError(f"{path.name}: pin positions must fit the body length.")
        for index, (side, offset) in enumerate(positions):
            if any(
                side == other_side and abs(offset - other_offset) < geometry.shoulder
                for other_side, other_offset in positions[index + 1:]
            ):
                raise ValueError(f"{path.name}: leads must not overlap.")
        reference = data["reference"]
        specification = Sot23Specification(
            body_width=PackageMeasurement(**reference["body_width"]),
            body_length=PackageMeasurement(**reference["body_length"]),
            lead_span=PackageMeasurement(**reference["lead_span"]),
            pin_pitch=PackageMeasurement(**reference["pin_pitch"]),
            source=data["source"],
        )
        variants[count] = Sot23Variant(count, geometry, specification, positions)
    if not variants:
        raise ValueError(f"No SOT-23 variant JSON files found in {directory}.")
    return tuple(variants[count] for count in sorted(variants))


SOT23_VARIANTS = load_variants(Path(__file__).resolve().with_name("variants"))
