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

# USBLC6-2SC6 SOT-23-6 Pinout

[JSON source](usblc6-2sc6.json) Â· [Horizontal SVG](usblc6-2sc6-horizontal.svg) Â·
[Vertical SVG](usblc6-2sc6-vertical.svg)

The STMicroelectronics USBLC6-2SC6 protects two data lines and VBUS against
electrostatic discharge (ESD). This entry covers the SOT23-6L version, viewed
from above with pin 1 beside the dot. It uses the repository's SOT-23-6 renderer.

Pin names and numbering follow the functional diagram on page 1 of the
[ST USBLC6-2 datasheet, DS4260 revision 7, December 2021](https://www.st.com/resource/en/datasheet/usblc6-2.pdf).

| Physical Pin | Datasheet Name | Diagram Type | Function |
| --- | --- | --- | --- |
| 1 | I/O1 | I/O | First terminal of protected data line 1 |
| 2 | GND | PWR | Ground reference |
| 3 | I/O2 | I/O | First terminal of protected data line 2 |
| 4 | I/O2 | I/O | Second terminal of protected data line 2 |
| 5 | VBUS | PWR | VBUS protection and upper clamp reference |
| 6 | I/O1 | I/O | Second terminal of protected data line 1 |

Pins 1 and 6 form one signal path; pins 3 and 4 form the other. The four data
terminals carry I/O badges because the protected signals can travel in either
direction. These are passive protection paths, not USB transceiver inputs and
outputs. The diagram retains I/O1 and I/O2 rather than assigning D+ and D-;
those assignments depend on board wiring.

See the functional diagram on page 1 and the PCB layout example in Figure 17
on page 11 for the paired paths. Section 2.3, page 6, describes placement near
the connector and short connections to the data lines, VBUS, and ground plane.

The package is ST's SOT23-6L, not the SOT-666 version used by USBLC6-2P6.
ST's package dimensions are in Table 3 on page 12. The drawing and its Package
block use the shared SOT-23-6 variant's TI reference outline; they are illustrative
and do not replace ST's mechanical tolerances or PCB footprint recommendations.

Landscape uses 60% content scale; portrait uses 50% to leave side margins. The JSON comments appear on both
SVGs. Regenerate the diagrams from this directory, or double-click `render.cmd`:

```powershell
.\render.cmd
```

The command works from other directories, uses the repository's `.venv` Python
when available, and otherwise uses `python` from PATH. Both orientations come
from the same JSON file, with the portrait scale override in `render.cmd`.
