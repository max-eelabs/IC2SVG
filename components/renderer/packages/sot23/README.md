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

# SOT-23 package family

Use `{"family": "SOT-23", "pin_count": 3}` in IC input JSON. Counts 3, 5,
and 6 are supported. The importable folder is `sot23`; the displayed family
and input identifier are `SOT-23`. Discovery and the existing input CLI load
this family automatically.

| Variant | Reference outline | Body length | Body width | Overall lead span | Same-side pitch |
| --- | --- | --- | --- | --- | --- |
| SOT-23-3 | Nexperia SOT23, TO-236AB | 2.80-3.00 mm | 1.20-1.40 mm | 2.10-2.50 mm | 1.90 mm |
| SOT-23-5 | TI DBV0005A, JEDEC MO-178 | 2.75-3.05 mm | 1.45-1.75 mm | 2.60-3.00 mm | 0.95 mm |
| SOT-23-6 | TI DBV0006A, JEDEC MO-178 | 2.75-3.05 mm | 1.45-1.75 mm | 2.60-3.00 mm | 0.95 mm |

Sources:

- [Nexperia SOT23 outline](https://assets.nexperia.com/documents/outline-drawing/SOT23.pdf#page=2),
  package information dated 12 October 2022, page 2.
- [TI DBV0005A outline](https://www.ti.com/lit/ds/symlink/tlv62565.pdf#page=23),
  TLV62565/66 datasheet package appendix, drawing 4214839/K, August 2024.
- [TI DBV0006A outline](https://www.ti.com/lit/pdf/mpds026q#page=1),
  drawing 4214840/G, August 2024.

These are selected manufacturer outlines, rather than a universal tolerance
set for every manufacturer's SOT-23. The 5- and 6-pin bodies are wider than the
classic 3-pin body. Thin SOT variants and smaller SC-70 packages are separate
outlines and are not represented here.

The drawing is a top view rotated to place pin 1 at the upper left. Pin numbers
run downward on the left, then upward on the right:

- 3 pins: left 1, 2; centered right 3.
- 5 pins: left 1, 2, 3; right 4 at the bottom and 5 at the top.
- 6 pins: left 1, 2, 3; right 4, 5, 6 from bottom to top.

For the 3-pin outline the two left pins are 1.90 mm apart; the opposite pin is
centered at a 0.95 mm offset from each. Five-pin right leads are also 1.90 mm
apart, with no physical center lead. The optional unnumbered molding support
shown in TI's five-pin drawing is not an electrical terminal.

Variant JSON stores explicit `(side, y_offset_mm)` positions in physical-number
order. Side -1 means left and +1 means right; offsets increase downward from
the body center. The catalog validates the schema, finite positive dimensions,
unique counts, complete positions, lead overlap, and body clearance before
rendering. Its schema intentionally accepts only counts 3, 5, and 6.

Reference tables preserve published millimeter ranges. Inch strings are fixed
rounded conversions to four decimal places, stored in the JSON assets; rendering
does not convert units. Illustration geometry uses nominal values or range
midpoints, with the same magnification across variants and orientations. Lead
span means outside-to-outside metal extent, not PCB land spacing. The bevel,
lead shading, and pin-one dot are illustrative. Electrical signal assignments
must come from the individual device datasheet.

Generate all installed package samples from the repository root:

```powershell
.\.venv\Scripts\python.exe -m components.renderer.packages.samples
.\.venv\Scripts\python.exe -m unittest discover -s components/renderer/packages/sot23/tests -t .
```

Dense portrait annotations may require a smaller `content_scale`, such as 0.4
for two short definition columns plus pin-type badges. Layouts that cannot fit
raise an error.

The six reproducible SVGs in [samples](samples/) use the fixed landscape and
portrait viewBoxes and the name `EXAMPLE`.
