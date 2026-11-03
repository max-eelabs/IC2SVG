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

# Narrow SOIC Package Family

Use `{"family": "SOIC", "pin_count": 8}` in IC input JSON. Counts 8, 14, and
16 select narrow-body packages with nominal 3.9 mm body width and 1.27 mm lead
pitch. Wide-body SOIC variants require separate support.

| Variant | TI Outline | Body Width | Body Length | Overall Lead Span |
| --- | --- | --- | --- | --- |
| SOIC-8 | D0008A | 3.81-3.98 mm | 4.81-5.00 mm | 5.80-6.19 mm |
| SOIC-14 | D0014A | 3.8-4.0 mm | 8.55-8.75 mm | 5.8-6.2 mm |
| SOIC-16 | D0016A | 3.8-4.0 mm | 9.8-10.0 mm | 5.8-6.2 mm |

Sources, all on page 1:

- [TI D0008A](https://www.ti.com/lit/ml/msoi002k/msoi002k.pdf#page=1),
  drawing 4214825/C, February 2019; JEDEC MS-012 variation AA.
- [TI D0014A](https://www.ti.com/lit/pdf/mpds177h#page=1),
  drawing 4220718/A, September 2016; JEDEC MS-012 variation AB.
- [TI D0016A](https://www.ti.com/lit/pdf/mpds432#page=1),
  drawing 4214828/B, August 2021; JEDEC MS-012.

SOIC-8 preserves the published inch values and their rounded millimeter values.
The metric SOIC-14 and SOIC-16 references store inch equivalents rounded to four
decimal places. Rendering displays these fixed strings without unit conversion.
The nominal illustration uses body lengths 4.9, 8.65, and 9.9 mm, a 6.0 mm lead
span, and 0.41 mm lead width. Reference ranges remain independent of geometry.
Lead span is the outside-to-outside metal extent, not PCB land spacing.

The drawing is a top view. Pin 1 is at the upper left, numbering proceeds down
the left side, then up the right side. The pin-one dot has a 57-unit diameter
and equal 42-unit top and left insets, matching the established package style.
The bevel, bend shading, and orientation dot are illustrative; consult the
specific manufacturer's drawing for marking and footprint details.

Geometry, reference data, schema, rendering, and plugin declaration are owned by
this folder. The catalog reads UTF-8 JSON assets in deterministic order and
returns variants sorted by physical pin count. It rejects unsupported counts,
duplicates, missing references, nonfinite or nonpositive dimensions, overlapping
leads, and leads extending beyond the body length. Imports do not render or write
files. Existing package discovery and packaging rules include this family and
its runtime assets automatically.

## Usage

```python
from components.renderer.packages.soic import SoicRenderer

SoicRenderer(14).render("EXAMPLE").save("soic14.svg")
```

For a complete pinout, use the existing JSON input CLI with a supported SOIC
count and definitions for every physical pin. The shared compositor supports
pin-type badges, function columns, legends, comments, and color overrides.
Dense portrait layouts may need a smaller `content_scale`; layouts that cannot
fit raise an error.

The six generic [SVG samples](samples/) use `EXAMPLE`, 60% content scale, and the
fixed 1920 x 1080 landscape or 1080 x 1920 portrait viewBox. Regenerate only this
family from the repository root:

```python
from components.renderer.packages.samples import generate_package_samples
from components.renderer.packages.soic.plugin import PACKAGE_PLUGIN

generate_package_samples(PACKAGE_PLUGIN, PACKAGE_PLUGIN.sample_directory)
```

Run its tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s components/renderer/packages/soic/tests -t .
```

These generic package samples contain the housing and physical pin numbers.
Complete collection pinouts add the Package, Legend, and Comments blocks through
the JSON compositor. Its optional `legend_columns` field and `--legend-columns`
CLI override control the legend independently of pin-function columns. See the
[layout guide](../../../../CONTRIBUTING.md#layout-and-legend-settings) for defaults,
single-line description limits, and sheet typography.
