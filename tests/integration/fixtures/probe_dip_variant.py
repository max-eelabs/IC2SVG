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

"""Exercise an added DIP variant in a fresh interpreter against an isolated copy.

The integration test copies this script beside its temporary components folder.
Run from that temporary root; SVGs and generated package samples are written
there, and a JSON report is printed to stdout for the parent test to verify.
"""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from components.input import parse_input
from components.renderer import Orientation
from components.renderer.packages.registry import get_package
from components.renderer.packages.samples import generate_all_samples


def _render_views(pin_count: int) -> list[str]:
    """Write both IC orientations into the working directory and report viewBoxes."""
    data = {
        "name": "EXTENDED",
        "package": {"family": "DIP", "pin_count": pin_count},
        "categories": {},
        "pins": [
            {"number": number, "type": "nc", "definitions": []}
            for number in range(1, pin_count + 1)
        ],
    }
    sizes = []
    for orientation in Orientation:
        data["orientation"] = orientation.name.lower()
        document = parse_input(data).render()
        document.save(Path(f"extended-{orientation.name.lower()}.svg"))
        view_box = ET.fromstring(document.to_string()).get("viewBox")
        if view_box is None:
            raise ValueError("Rendered SVG is missing its logical viewBox.")
        sizes.append(view_box)
    return sizes


def main() -> None:
    """Render the requested count, generate samples, and emit a JSON report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pin_count", type=int)
    arguments = parser.parse_args()
    count = arguments.pin_count
    sizes = _render_views(count)
    paths = generate_all_samples()
    print(json.dumps({
        "counts": get_package("DIP").pin_counts,
        "new_samples": sorted(
            path.name for path in paths if path.name.startswith(f"dip{count}-")
        ),
        "sizes": sizes,
    }))


if __name__ == "__main__":
    main()
