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

"""Generate SVG samples for all discovered families and supported pin counts."""

from pathlib import Path

from ..core import Orientation
from .registry import PackagePlugin, discover_packages


def generate_package_samples(
    plugin: PackagePlugin, output_directory: str | Path
) -> tuple[Path, ...]:
    """Write a family's variants in ascending count and orientation order.

    Creates the target directory and replaces matching SVG files. All dimensions
    and layout behavior are supplied by the plugin. No concrete ICs are generated.
    """
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for count in plugin.pin_counts:
        renderer = plugin.create_renderer(count)
        for orientation in Orientation:
            document = renderer.render("EXAMPLE", orientation)
            filename = f"{plugin.family.lower()}{count}-{orientation.name.lower()}.svg"
            path = output / filename
            document.save(path)
            paths.append(path)
    return tuple(paths)


def generate_all_samples(
    output_directory: str | Path | None = None,
) -> tuple[Path, ...]:
    """Generate every discovered variant in both orientations.

    With no directory, writes into each plugin's declared sample_directory.
    Otherwise creates one lowercase family subdirectory under the given root.
    Existing matching samples are replaced; unrelated files are retained.
    """
    paths = []
    for plugin in discover_packages():
        output = (
            plugin.sample_directory if output_directory is None
            else Path(output_directory) / plugin.family.lower()
        )
        paths.extend(generate_package_samples(plugin, output))
    return tuple(paths)


def main() -> None:
    """Regenerate package-owned SVG samples for every installed package family."""
    generate_all_samples()


if __name__ == "__main__":
    main()
