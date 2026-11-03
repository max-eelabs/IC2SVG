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

"""Fixed package reference measurements from per-variant DIP JSON assets.

Both units retain source precision and ranges. For the millimeter-only DIP-4
outline, inch values are pretabulated rounded equivalents. Reference data is
independent of illustration geometry and is never converted at render time.
"""

from .catalog import DIP_VARIANTS, DipSpecification, PackageMeasurement


_SPECIFICATIONS = {
    variant.pin_count: variant.specification for variant in DIP_VARIANTS
}

__all__ = ["DipSpecification", "PackageMeasurement", "dip_specification"]


def dip_specification(pin_count: int) -> DipSpecification:
    """Return fixed source measurements for one supported DIP pin count.

    Raises:
        ValueError: The pin count has no supported reference outline.
    """
    if type(pin_count) is not int or pin_count not in _SPECIFICATIONS:
        raise ValueError(f"No reference dimensions for DIP-{pin_count}.")

    return _SPECIFICATIONS[pin_count]
