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

"""Self-contained extension declaration, copied into a temporary package folder."""

from pathlib import Path

from components.renderer.packages.registry import PackagePlugin

from .renderer import AddonPinoutRenderer, AddonRenderer


PACKAGE_PLUGIN = PackagePlugin(
    family="TEST_ADDON",
    pin_counts=(2, 32),
    renderer_factory=AddonRenderer,
    sample_directory=Path(__file__).resolve().with_name("samples"),
    pinout_factory=AddonPinoutRenderer,
)
