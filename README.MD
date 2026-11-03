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

# IC2SVG

IC2SVG turns JSON IC definitions into clear, reproducible SVG pinout diagrams
for documentation, presentations, and electronics reference. The goal is to
make accurate pinout diagrams easy to create, maintain, and share.

Licensed under [Apache 2.0](LICENSE). [NOTICE](NOTICE) also covers all generated
SVG images in the repository.

Browse the [IC catalogue and render presets](collection/README.md), the
[ATtiny85 pinout](collection/MCU/ATTiny85/README.md), or the
[PIC16F1454 pinout](collection/MCU/PIC16F1454/README.md).

## Technology

- **Python 3.10+** for package geometry, layout, and rendering.
- **Pillow and fontTools** for font measurement and vector text outlines.
- **JSON Schema / jsonschema** for validating IC definitions and package data.
- **SVG** for scalable horizontal and vertical diagrams.

| Package family | Supported physical pin counts |
| --- | --- |
| [DIP](components/renderer/packages/dip/) | 4, 6, 8, 14, 16, 18, 20, 24, 28 |
| [SOT-23](components/renderer/packages/sot23/README.md) | 3, 5, 6 |
| [Narrow SOIC](components/renderer/packages/soic/README.md) | 8, 14, 16 |

## Render a Diagram

Install the project in your Python environment, then render an existing entry:

```powershell
python -m pip install .
python -m components.input collection/USB/AP2151DWG-7/ap2151dwg-7.json ap2151dwg-7.svg --orientation landscape
```

Each collection entry also has a `render.cmd` that regenerates both orientations
with its saved scale and legend settings. SVG output uses vector font outlines,
a fixed viewBox, and explicit UTF-8 encoding with LF line endings.

The optional JSON field `legend_columns` defaults to `null` for automatic
layout. Use `--legend-columns 1` or another count to override it for one render.
Package, Legend, and Comments text stays at a fixed sheet size when the chip's
`content_scale` changes. See the [layout instructions](CONTRIBUTING.md#layout-and-legend-settings)
for defaults and examples.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for adding ICs to the
[collection](collection/), supporting packages and variants, and running tests.

## Let's build it together

Would IC2SVG be useful to you? Help shape it by contributing IC definitions,
adding package support, improving layouts, or sharing what you need from it.

Contact **Maxim Pavlov** at [pavlov.web@gmail.com](mailto:pavlov.web@gmail.com)
to collaborate.
