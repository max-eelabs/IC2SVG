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

"""Discover self-contained package plugins without a central family list.

Each immediate package folder may supply plugin.py exposing PACKAGE_PLUGIN.
Discovery imports trusted local Python code, in sorted module-name order; JSON
input only selects a discovered family and can never request arbitrary imports.
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from pkgutil import iter_modules
import re

from ..core import IcRenderer
from ..pinout import PinoutRenderer


@dataclass(frozen=True)
class PackagePlugin:
    """Declare one family, its supported counts, and package-owned rendering.

    renderer_factory creates fresh IcRenderer instances for each pin count.
    sample_directory points to this plugin's samples folder. The default pinout
    factory supports left/right pins; other arrangements supply a PinoutRenderer
    subclass with their layout strategy, entirely within the new package folder.
    """

    family: str
    pin_counts: tuple[int, ...]
    renderer_factory: Callable[[int], IcRenderer]
    sample_directory: Path
    pinout_factory: Callable[[IcRenderer], PinoutRenderer] = PinoutRenderer

    def __post_init__(self) -> None:
        """Validate plugin metadata without constructing renderers or writing files."""
        if not isinstance(self.family, str) or not re.fullmatch(
            r"[A-Z][A-Z0-9_-]*", self.family
        ):
            raise ValueError("Package family must be an uppercase identifier.")
        if (
            not isinstance(self.pin_counts, tuple) or not self.pin_counts
            or any(type(count) is not int or count <= 0 for count in self.pin_counts)
            or self.pin_counts != tuple(sorted(set(self.pin_counts)))
        ):
            raise ValueError(
                "Package pin counts must be sorted, unique positive integers."
            )
        if not callable(self.renderer_factory) or not callable(self.pinout_factory):
            raise TypeError("Package renderer factories must be callable.")
        if not isinstance(self.sample_directory, Path):
            raise TypeError("Package sample_directory must be a Path.")

    def create_renderer(self, pin_count: int) -> IcRenderer:
        """Create a supported renderer, rejecting invalid or inconsistent variants."""
        if type(pin_count) is not int or pin_count not in self.pin_counts:
            counts = ", ".join(str(count) for count in self.pin_counts)
            raise ValueError(
                f"Unsupported {self.family} pin count {pin_count}. Supported: {counts}."
            )

        renderer = self.renderer_factory(pin_count)
        if not isinstance(renderer, IcRenderer) or renderer.pin_count != pin_count:
            raise ValueError(
                f"{self.family} factory returned an inconsistent renderer."
            )
        if not renderer.reference_dimensions:
            raise ValueError(f"{self.family}-{pin_count} needs reference dimensions.")
        return renderer


def discover_packages() -> tuple[PackagePlugin, ...]:
    """Find package folders with plugin.py and return plugins ordered by family.

    No mutable registry or cached family list is retained. Folders without a
    plugin module are ignored. Duplicate families and invalid exports raise an
    error; import failures inside a plugin propagate rather than hiding a package.
    """
    namespace = import_module(__package__)
    modules = sorted(
        iter_modules(namespace.__path__, prefix=namespace.__name__ + "."),
        key=lambda item: item.name,
    )
    discovered: dict[str, PackagePlugin] = {}
    for candidate in modules:
        if not candidate.ispkg or candidate.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        module_name = candidate.name + ".plugin"
        if find_spec(module_name) is None:
            continue
        plugin = getattr(import_module(module_name), "PACKAGE_PLUGIN", None)
        if not isinstance(plugin, PackagePlugin):
            raise ValueError(
                f"{module_name} must export a PackagePlugin as PACKAGE_PLUGIN."
            )
        if plugin.family in discovered:
            raise ValueError(f"Duplicate package family: {plugin.family}.")
        discovered[plugin.family] = plugin
    return tuple(discovered[family] for family in sorted(discovered))


def get_package(family: str) -> PackagePlugin:
    """Resolve an installed family or report the available families in an error."""
    plugins = discover_packages()
    for plugin in plugins:
        if plugin.family == family:
            return plugin

    supported = ", ".join(plugin.family for plugin in plugins) or "none installed"
    raise ValueError(f"Unsupported package family {family!r}. Supported: {supported}.")
