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

# IC Catalogue

Each entry contains a JSON definition, horizontal and vertical SVGs, a README
with datasheet references, and a `render.cmd` regeneration script.

| Category | Entry | Package | Landscape scale | Portrait scale | Portrait legend |
| --- | --- | --- | --- | --- | --- |
| AMP | [INA240A2DR](AMP/INA240A2DR/README.md) | SOIC-8 | 60% | 50% | Automatic |
| MCU | [ATtiny85](MCU/ATTiny85/README.md) | DIP-8 | 35% | 20% | 1 column |
| MCU | [PIC16F1454](MCU/PIC16F1454/README.md) | DIP-14 | 33.95% | 14% | 2 columns |
| OPT | [ISO1540DR](OPT/ISO1540DR/README.md) | SOIC-8 | 60% | 50% | Automatic |
| USB | [AP2151DWG-7](USB/AP2151DWG-7/README.md) | SOT-23-5 | 60% | 50% | Automatic |
| USB | [USBLC6-2SC6](USB/USBLC6-2SC6/README.md) | SOT-23-6 | 60% | 50% | Automatic |

Landscape uses the JSON's `content_scale`. Portrait scale and explicit legend
columns are stored as CLI overrides in each `render.cmd`. Every current JSON
uses `"legend_columns": null`, which selects automatic layout unless overridden.
Automatic legends have at most four entries per column. An explicit column count
balances entries across that many columns and can have more than four rows.

From the repository root, regenerate an entry with its saved settings:

```powershell
.\collection\MCU\ATTiny85\render.cmd
```

The script can also be run from its own folder or by double-clicking it. It uses
the repository's `.venv` Python when available and falls back to `python` on PATH.
It replaces that entry's two SVGs. Other entries and PNG previews are unaffected.

To render a separate portrait without modifying the JSON or stored SVGs:

```powershell
python -m components.input collection/MCU/ATTiny85/attiny85.json attiny85-portrait.svg --orientation portrait --content-scale 0.2 --legend-columns 1
```

Content scale changes the chip, pin numbers, and function definitions together.
It does not resize the Package, Legend, or Comments blocks. Legend descriptions
stay on one line and receive `...` if they exceed 24 characters or their available
width. Full category descriptions remain in the JSON. Comments may wrap.

See [Contributing](../CONTRIBUTING.md) for the input format, legend configuration,
adding devices and package families, and validation. Concrete device pinouts
belong here; generic package samples remain under `components/renderer/packages/`.
