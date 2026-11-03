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

"""Deterministic IC package rendering."""

from .core import (
    IcRenderer, Orientation, PackageDimension, PackageLayout, Pin, Rectangle,
    SvgDocument,
)
from .comments import BottomLeftCommentsRenderer, CommentsRenderer
from .packages.dip import DipRenderer
from .definition import (
    DefinitionRenderer, DefinitionSize, PinDefinition, RoundedDefinitionRenderer,
)
from .line import LineRenderer, StraightLineRenderer
from .legend import LegendEntry, LegendRenderer, TopRightLegendRenderer
from .pinout import PinLabel, PinoutRenderer, PinType
from .package_info import TopLeftPackageRenderer

__all__ = [
    "BottomLeftCommentsRenderer",
    "CommentsRenderer",
    "DipRenderer",
    "DefinitionRenderer",
    "DefinitionSize",
    "IcRenderer",
    "LineRenderer",
    "LegendEntry",
    "LegendRenderer",
    "Orientation",
    "PackageDimension",
    "PackageLayout",
    "Pin",
    "PinDefinition",
    "PinLabel",
    "PinoutRenderer",
    "PinType",
    "Rectangle",
    "RoundedDefinitionRenderer",
    "StraightLineRenderer",
    "SvgDocument",
    "TopRightLegendRenderer",
    "TopLeftPackageRenderer",
]
