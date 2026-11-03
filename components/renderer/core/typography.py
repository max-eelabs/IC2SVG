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

"""Shared text sizes and visible spacing in logical SVG drawing units."""

DEFINITION_SCALE = 1.716

LABEL_FONT_SIZE = 28 * DEFINITION_SCALE

PIN_NUMBER_GAP = 28.0

# Overlay headings use sheet units, independent of each block's drawing scale.
HEADING_FONT_SIZE = 30

HEADING_CONTENT_GAP = 12.0

# Overlay body text and row spacing are independent of the IC content scale.
OVERLAY_FONT_SIZE = 22

OVERLAY_ROW_HEIGHT = 32.0

HEADING_POSITION_Y = 12.0

# Increase both legend samples and their outlines without changing pin labels.
LEGEND_SCALE = 0.5

# Legend samples are slightly smaller than the surrounding descriptions.
LEGEND_DEFINITION_SCALE = 0.9

# Legend descriptions stay on one line; longer text receives an ellipsis.
LEGEND_DESCRIPTION_MAX_CHARS = 24
