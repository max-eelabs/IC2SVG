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

# AP2151DWG-7 SOT-23-5 Pinout

[JSON source](ap2151dwg-7.json) · [Horizontal SVG](ap2151dwg-7-horizontal.svg) ·
[Vertical SVG](ap2151dwg-7-vertical.svg)

The Diodes Incorporated AP2151DWG-7 is an AP2151D USB power switch with output
discharge. Package code W selects SOT25, rendered here with the SOT-23-5 family.
The drawing is a top view, with pin 1 beside the dot.

Pin assignments follow pages 1-2 of the
[AP2141D/AP2151D datasheet, DS32242 revision 6-2, March 2015](https://www.diodes.com/datasheet/download/AP2151D.pdf).
The ordering code is listed on page 12.

| Pin | Name | Diagram Type | Function |
| --- | --- | --- | --- |
| 1 | OUT | PWR | Switched power output |
| 2 | GND | PWR | Ground |
| 3 | FLG | OUT | Active-low, open-drain fault output |
| 4 | EN | IN | Active-high enable input |
| 5 | IN | PWR | Supply input |

The FLG overbar is encoded as `~FLG` in JSON. Use an external pull-up for this
open-drain signal; it reports overcurrent and overtemperature faults. EN has no
overbar because AP2151D uses active-high enable. PWR badges distinguish power
terminals from the logic input and output. This is a power switch, not a USB
data transceiver.

The shared renderer's Package block uses TI reference dimensions. For this
part's mechanical data and recommended PCB lands, see the manufacturer's SOT25
outline on page 15 and pad layout on page 16.

Landscape uses 60% content scale and portrait uses 50%. Comments appear on
both drawings. Regenerate both SVGs from this directory, or double-click
`render.cmd`:

```powershell
.\render.cmd
```

The script works from other directories and uses the repository's `.venv`
Python when available, otherwise `python` from PATH. The portrait scale override
is stored in the script; both diagrams use the same JSON source.
