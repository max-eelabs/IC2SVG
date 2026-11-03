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

# ISO1540DR SOIC-8 Pinout

[JSON source](iso1540dr.json) · [Horizontal SVG](iso1540dr-horizontal.svg) ·
[Vertical SVG](iso1540dr-vertical.svg)

ISO1540DR is a bidirectional I2C isolator in TI's D (narrow SOIC-8) package.
It is filed under OPT for the collection's isolation category; its isolation
technology is capacitive, not optical. The diagram is a top view with pin 1
beside the dot.

Pin assignments follow Figure 5-1 and Table 5-1 on page 4 of the
[TI ISO1540/ISO1541 datasheet, SLLSEB6F, December 2022](https://www.ti.com/lit/ds/symlink/iso1540.pdf#page=4).

| Pin | Name | Diagram Type | Function |
| --- | --- | --- | --- |
| 1 | VCC1 | PWR | Side 1 supply |
| 2 | SDA1 | I/O | Side 1 data |
| 3 | SCL1 | I/O | Side 1 clock |
| 4 | GND1 | PWR | Side 1 ground |
| 5 | GND2 | PWR | Side 2 ground |
| 6 | SCL2 | I/O | Side 2 clock |
| 7 | SDA2 | I/O | Side 2 data |
| 8 | VCC2 | PWR | Side 2 supply |

Side numbers remain part of every signal name. Ground pins belong to separate
isolation domains. Both clock and data channels are bidirectional on ISO1540;
ISO1541 has different clock-direction behavior and is not represented here.
The two I2C sides use separate function colors while retaining I/O badges.

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
