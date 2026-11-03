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

"""Pin definition content independent of its visual rendering."""

from dataclasses import dataclass

from PIL import ImageColor


@dataclass(frozen=True)
class PinLabel:
    """Text and category colors for one physical pin's annotation."""

    text: str
    color: str = "#E0E0E0"
    text_color: str = "#202020"

    def __post_init__(self) -> None:
        """Validate label text and explicit colors before rendering."""
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Pin label must have nonempty text.")
        if any(char in self.text for char in "\r\n\t"):
            raise ValueError("Pin label must occupy one line.")
        for color in (self.color, self.text_color):
            ImageColor.getrgb(color)


@dataclass(frozen=True)
class PinDefinition:
    """One definition in an explicit outward column, starting at one."""

    column: int
    label: PinLabel

    def __post_init__(self) -> None:
        """Reject ambiguous column indexes and unsupported labels."""
        if type(self.column) is not int or not 1 <= self.column <= 16:
            raise ValueError("Definition column must be an integer in 1..16.")
        if not isinstance(self.label, PinLabel):
            raise TypeError("Definition label must be a PinLabel.")
