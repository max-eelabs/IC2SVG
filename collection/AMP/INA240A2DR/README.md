<!--
Copyright 2026 Maxim Pavlov <pavlov.web@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
-->

# INA240A2DR SOIC-8 Pinout

[JSON source](ina240a2dr.json) · [Horizontal SVG](ina240a2dr-horizontal.svg) ·
[Vertical SVG](ina240a2dr-vertical.svg)

This INA240 entry selects INA240A2DR: the A2 current-sense amplifier with
50 V/V gain in TI's D (narrow SOIC-8) package. The diagram is a top view,
with pin 1 beside the dot.

Pin assignments follow Figure 6-2 and Table 6-1 on page 3 of the
[TI INA240 datasheet, SBOS662C, December 2021](https://www.ti.com/lit/ds/symlink/ina240.pdf#page=3).
The TSSOP version uses a different pin assignment.

| Pin | Name | Diagram Type | Function |
| --- | --- | --- | --- |
| 1 | IN- | IN | Negative shunt input |
| 2 | GND | PWR | Ground |
| 3 | REF2 | IN | Reference input 2 |
| 4 | NC | NC | No internal connection |
| 5 | OUT | OUT | Analog voltage output |
| 6 | VS | PWR | Supply |
| 7 | REF1 | IN | Reference input 1 |
| 8 | IN+ | IN | Positive shunt input |

IN- uses an ASCII minus sign to denote input polarity, not an active-low signal.
REF1 and REF2 set the output reference. Pin 4 may be grounded or left floating,
as specified in Table 6-1. Power, analog signals, reference inputs, and NC use
separate function categories; electrical type badges remain independent.

The drawing uses the shared SOIC-8 renderer and its TI reference dimensions.
Landscape uses 60% content scale; portrait uses 50% for side margins. Comments
appear on both diagrams. Regenerate both SVGs from this directory, or double-click
`render.cmd`:

```powershell
.\render.cmd
```

The script works from other directories and uses the repository's `.venv`
Python when available, otherwise `python` from PATH. The portrait scale override
is stored in the script; both SVGs use the same JSON source.
