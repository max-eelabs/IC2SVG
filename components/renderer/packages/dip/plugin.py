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

"""Declare the DIP family for automatic discovery and sample generation."""

from pathlib import Path

from ..registry import PackagePlugin
from .renderer import SUPPORTED_PIN_COUNTS, DipRenderer


PACKAGE_PLUGIN = PackagePlugin(
    family="DIP",
    pin_counts=SUPPORTED_PIN_COUNTS,
    renderer_factory=DipRenderer,
    sample_directory=Path(__file__).resolve().with_name("samples"),
)
