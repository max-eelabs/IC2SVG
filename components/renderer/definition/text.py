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

"""Interpret signal-name notation independently of SVG drawing."""

from dataclasses import dataclass
import re


_ACTIVE_LOW = re.compile(r"~([^\s/~]+)")


@dataclass(frozen=True)
class SignalText:
    """Visible text and half-open character ranges that require an overbar."""

    text: str
    overbars: tuple[tuple[int, int], ...]


def parse_signal_text(source: str) -> SignalText:
    """Convert ~NAME into an overbar range ending at a slash or whitespace.

    Examples:
        ~RESET/dW decorates RESET only; OC0A/~OC1A decorates OC1A only.

    Raises:
        ValueError: A tilde is not followed by a signal name.
    """
    pieces = []
    ranges = []
    previous = 0
    length = 0
    for match in _ACTIVE_LOW.finditer(source):
        literal = source[previous:match.start()]
        if "~" in literal:
            raise ValueError("Active-low marker '~' must precede a signal name.")
        pieces.append(literal)
        length += len(literal)
        signal = match.group(1)
        pieces.append(signal)
        ranges.append((length, length + len(signal)))
        length += len(signal)
        previous = match.end()
    suffix = source[previous:]
    if "~" in suffix:
        raise ValueError("Active-low marker '~' must precede a signal name.")
    pieces.append(suffix)
    return SignalText("".join(pieces), tuple(ranges))
