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

"""Render a validated JSON pinout as SVG from the command line."""

import argparse
from dataclasses import replace

from components.renderer import Orientation

from .loader import load_input


def main() -> None:
    """Load a definition and write SVG, reporting expected input errors concisely."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input file")
    parser.add_argument("output", help="SVG output file")
    parser.add_argument(
        "--orientation", choices=("landscape", "portrait"),
        help="Override the JSON orientation for this render",
    )
    parser.add_argument(
        "--content-scale", type=float,
        help="Override the JSON drawing scale (greater than zero, at most one)",
    )
    args = parser.parse_args()
    try:
        pinout = load_input(args.input)
        if args.orientation is not None:
            pinout = replace(pinout, orientation=Orientation[args.orientation.upper()])
        if args.content_scale is not None:
            pinout = replace(pinout, content_scale=args.content_scale)
        pinout.render().save(args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
