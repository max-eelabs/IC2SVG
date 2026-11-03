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

# Contributing

## Commit requirements

Every contributed commit must include both a sign-off and a cryptographic
signature. Configure your Git author identity and signing key, then commit with:

```sh
git commit -s -S -m "Describe your change"
```

- `-s` adds a `Signed-off-by` trailer using your Git committer identity.
- `-S` signs the commit with your configured signing key.

Both are required for code, documentation, IC definitions, and generated SVGs.
See the [Git commit documentation](https://git-scm.com/docs/git-commit) for the
sign-off and signing options.

## License headers

Project contributions use the [Apache License 2.0](LICENSE). Add source headers
with [Google addlicense](https://github.com/google/addlicense). From the root:

```sh
addlicense -l apache -s -y 2026 -c "Maxim Pavlov <pavlov.web@gmail.com>" -ignore ".git/**" -ignore ".venv/**" -ignore "tmp/**" -ignore "**/__pycache__/**" .
addlicense -check -ignore ".git/**" -ignore ".venv/**" -ignore "tmp/**" -ignore "**/__pycache__/**" .
```

The project uses `addlicense` v1.2.0. Use the appropriate copyright year for new
contributions. The tool checks supported source formats, including Python and
TOML. Preserve any existing third-party attribution.

JSON assets and generated SVGs are covered collectively by [NOTICE](NOTICE).
Keep JSON valid and let SVGs remain reproducible renderer outputs; individual
image listings or per-image license headers are not needed. Markdown and command
files use license comments matching their file syntax. Include `LICENSE` and
`NOTICE` when distributing project materials.

## Contribution workflows

Add an IC through its collection files. For an existing package family and pin
count, its JSON is enough to render it without Python code changes. A new DIP
variant needs one package JSON asset; a new family needs its own package folder
and plugin. These workflows are described below.

## How to add IC to the collection

### Create the collection entry

Create `collection/<category>/<IC name>/`, using the existing
[ATTiny85 entry](collection/MCU/ATTiny85/) as a structure reference. For example:

```text
collection/MCU/MyIC/
    my-ic.json
    my-ic-horizontal.svg
    my-ic-vertical.svg
    README.md
    render.cmd
```

Keep the JSON, both generated SVGs, notes, and regeneration command together.
Choose the category that matches the device and use consistent filenames within
the entry. Generic package samples remain in their package's `samples/` folder.

### Define the IC in JSON

Follow the [IC input schema](components/input/schema.json). You can copy an
existing collection JSON as a starting point, then replace its name, package,
categories, pin assignments, and comments using the new IC's datasheet.

| Field | Required content |
| --- | --- |
| `name` | The IC name displayed on the housing |
| `package` | An installed `family` and supported `pin_count`, such as `{"family": "DIP", "pin_count": 8}` |
| `categories` | Function category IDs with display names and optional colors; `{}` is valid when there are no function definitions |
| `pins` | Every physical pin exactly once, numbered from 1 through `pin_count` |
| Each pin's `type` | `input`, `output`, `io`, `power`, or `nc` |
| Each pin's `definitions` | An array of function definitions, or `[]` when none apply |

Each function definition needs `column`, `category`, and `name`. Use unique
columns 1 through 16 per pin; columns count outward after the mandatory gray
pin-type badge. Empty slots retain their space. Declare every referenced category
in `categories`; optional `color` and `text_color` values use `#RRGGBB` strings.
Prefix active-low signals with `~` for an overbar.

### Layout and Legend Settings

These optional fields control presentation without changing physical pin data:

| Field | Default | Meaning |
| --- | --- | --- |
| `orientation` | `"landscape"` | `"landscape"` or `"portrait"` |
| `content_scale` | `0.6` | Uniform chip and pin-definition scale, greater than zero and at most one |
| `legend_columns` | `null` | Automatic legend layout, or an explicit integer from 1 through 16 |
| `comments` | `[]` | Ordered explanatory notes at the bottom left; long notes wrap |

Existing JSON files may omit `legend_columns`. Omission and `null` both select
columns filled downward with at most four entries each. An explicit count
balances entries across the requested columns, with earlier columns receiving
any extra entries. Counts above the entry count do not create empty columns.
The four-row limit applies only to automatic layout.

For example, these display fields can be added to a complete IC definition:

```json
{
  "orientation": "landscape",
  "content_scale": 0.6,
  "legend_columns": null,
  "comments": []
}
```

The CLI options `--orientation`, `--content-scale`, and `--legend-columns` override
the corresponding JSON values for one render. They do not modify the source file.
Use orientation-specific overrides in `render.cmd`: ATtiny85 portrait requests
one legend column, while PIC16F1454 portrait requests two. Exact collection presets
are listed in the [IC catalogue](collection/README.md).

Legend descriptions remain on one line. Text longer than 24 characters or its
available width is shortened with `...`, including the dots in the limit. Only
the displayed category description is shortened; JSON category names, pin
functions, and legend sample labels remain intact. Comments wrap independently.
Rows retain the same height for short and shortened legend descriptions.

The standard compositor reserves the Package block's bounds and moves the
legend below it if the two blocks would overlap. A custom legend renderer owns
its own placement. In Python, `TopRightLegendRenderer(columns=2,
description_max_chars=18)` selects two columns and a shorter description limit.
The limit must be an integer of at least four; this is a Python option, not a
JSON field or CLI flag.

Shared sheet typography is configured in
[typography.py](components/renderer/core/typography.py): headings are 30 logical
units and body text is 22. The legend's sample labels and colored boxes use 90%
of the standard definition size inside the legend, with a font size of about 21.6
sheet units. This does not resize the chip's function labels. Changing
`content_scale` scales the chip and its pin annotations together; Package,
Legend, and Comments remain at their sheet sizes. Changing SVG export `scale`
changes the viewport uniformly while preserving the logical viewBox.

For the three-level collection structure above, the optional editor schema link
is:

```json
"$schema": "../../../components/input/schema.json"
```

Confirm the exact package variant and every physical pin against the datasheet,
including power, ground, unused pins, alternate functions, and pin-one direction.
If the required family or count is missing, follow the package or variant
instructions later in this guide before rendering the IC.

### Add a regeneration command

Copy [render.cmd](collection/MCU/ATTiny85/render.cmd) into the new entry and update
its JSON and SVG filenames. Keep its directory handling and error checks so it
works when launched from another directory or by double-clicking on Windows.
The script uses the repository's `.venv` Python when available, otherwise
`python` from PATH. Its root-relative directory handling assumes the
`collection/<category>/<IC name>/` structure shown above.

Generate both orientations from the same JSON. From the repository root, the
equivalent commands are:

```powershell
.\.venv\Scripts\python.exe -m components.input collection/MCU/MyIC/my-ic.json collection/MCU/MyIC/my-ic-horizontal.svg --orientation landscape
.\.venv\Scripts\python.exe -m components.input collection/MCU/MyIC/my-ic.json collection/MCU/MyIC/my-ic-vertical.svg --orientation portrait --content-scale 0.2 --legend-columns 1
```

The horizontal command uses the JSON's content scale. Choose a suitable vertical
scale and legend layout for the new IC; 0.2 and one legend column are the dense
ATtiny85 portrait settings, not requirements for every device. Store all
orientation-specific overrides in `render.cmd` so
regeneration is repeatable. CLI overrides do not modify the source JSON.

Inside the entry, regenerate both files with:

```powershell
.\render.cmd
```

### Document and review the entry

In its `README.md`, link the JSON and both SVGs, cite the datasheet and relevant
revision or pages, describe the selected package, and explain any pin-function
caveats. Include the regeneration command. Keep source-backed IC notes with the
collection entry.

Run the command and inspect both SVGs for readable labels, correct physical
numbering, pin-one orientation, complete alternate functions, and unclipped
legends and comments. Confirm the required type badge is first on every pin and
that power and NC pins are represented. Rerun the command and check that the
outputs are unchanged. Include all five entry files in the contribution.

### Regenerate Collection and Package Samples

Collection SVGs are regenerated by their entry's `render.cmd`. To regenerate
all current collection entries from PowerShell at the repository root:

```powershell
Get-ChildItem collection -Recurse -Filter render.cmd | ForEach-Object {
    & $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Rendering failed: $($_.FullName)" }
}
```

The package sample generator is separate:

```powershell
python -m components.renderer.packages.samples
```

It writes generic `EXAMPLE` drawings for all installed package variants. It does
not regenerate collection pinouts or PNGs.

SVGs are saved as UTF-8 with an explicit matching XML declaration and LF line
endings. Git preserves LF for SVGs through `.gitattributes`. Compare repeated
renders byte for byte; when checking older stored SVGs, parsed XML comparisons
can ignore legacy encoding declarations while still comparing drawing content.

## Add a variant to an existing family

### DIP variants

1. Find the manufacturer's package outline for the exact variant, including its
   pin count and body-width option. Record the source and page or drawing number.
2. Add a JSON file such as `dip<count>.json` under
   [components/renderer/packages/dip/variants/](components/renderer/packages/dip/variants/).
   Use [dip8.json](components/renderer/packages/dip/variants/dip8.json) as a format
   reference, replacing its values with the new variant's specification.
3. Fill in all required fields:

   | Field | Content |
   | --- | --- |
   | `pin_count` | A unique, even integer of at least four |
   | `geometry_mm` | Numeric illustrative dimensions in millimeters: `width`, `length`, `span`, `shoulder`, `tip`, and `pitch` |
   | `reference.body_width` | Published body width as explicit `inches` and `millimeters` strings |
   | `reference.body_length` | Published body length in both units |
   | `reference.lead_span` | Published free-lead span in both units |
   | `reference.pin_pitch` | Published adjacent-pin pitch in both units |
   | `source` | A specification reference, preferably a direct URL with its page |

4. Run the validation and sample-generation steps below. Inspect the new variant
   in both orientations and add tests for its specific geometry and numbering.

The [variant schema](components/renderer/packages/dip/variant.schema.json) and
catalog enforce positive, finite geometry. Lead span must exceed body width,
lead-tip width must not exceed shoulder width, and shoulder width must be smaller
than pin pitch. Duplicate counts and incomplete reference measurements fail
validation before rendering.

Keep reference measurements separate from illustrative geometry. Store inches
first and millimeters second as explicit source text; rendering does not convert
units. Preserve published precision and ranges instead of replacing ranges with
calculated midpoints. Free-lead span is distinct from PCB row spacing. If the
source provides only millimeters, document that the stored inch equivalents are
rounded conversions.

The renderer may enlarge a short body for pin clearance or shorten leads for
clarity. Those drawing adjustments must not change the displayed reference
measurements. Layouts that cannot fit legibly must report an error.

The DIP catalog reads every `variants/*.json` file at application startup.
`SUPPORTED_PIN_COUNTS`, JSON loading, and sample generation pick up the new count
automatically. Start a fresh process after adding an asset; no Python file or
central supported-count list needs editing.

### Variants in other families

Use that family's package-owned variant format. New families should provide a
catalog that discovers their variant assets and derives the plugin's supported
counts from them, following the DIP implementation. The shared system does not
assume that another family's geometry uses DIP fields or numbering rules.

## Add a new package family

### Create the package folder

Create a folder immediately under `components/renderer/packages/`, for example:

```text
components/renderer/packages/soic/
    __init__.py
    renderer.py
    plugin.py
    variants/             # Optional package-owned JSON variant data.
    variant.schema.json   # Validation for that data, if used.
    samples/              # Generated generic package SVGs.
```

The folder must contain `__init__.py` for Python imports and build discovery.
Keep its geometry, fixed specification data, and any custom annotation strategy
inside this folder. Reference data may also live in its Python modules.

### Implement the renderer contract

Subclass [IcRenderer](components/renderer/core/renderer.py) and implement:

| Member | Contract |
| --- | --- |
| `pin_count` | Total physical pins in the selected variant |
| `reference_dimensions` | An ordered, nonempty tuple of `PackageDimension(label, inches, millimeters)` rows from fixed specification data |
| `package_layout(orientation)` | A `PackageLayout` with body bounds and pins ordered by physical numbers 1 through N |
| `pin_number_bounds(pin, layout)` | Exact visible number bounds for annotation placement |
| `render_pins(document, layout)` | Metal pins and their physical numbers, in numeric order |
| `render_package(document, layout, ic_name)` | Housing, orientation marker, and the requested name |

Coordinates are logical SVG units: x increases rightward and y downward. Use the
shared `SvgDocument` and fixed fonts. The logical viewBox is 1920 x 1080 for
landscape or 1080 x 1920 for portrait; scale geometry, strokes, and lettering
uniformly. Keep ordering explicit and output deterministic. Do not write files
or render samples during module import.

Use the existing `IcRenderer.render()` implementation to create documents.
Preserve the meaning of physical numbers, pin types, function categories, and
board aliases separately. Pin-type badges remain first, nearest the package,
before outward function columns.

### Declare the plugin

Add `plugin.py` exporting one `PackagePlugin` instance named `PACKAGE_PLUGIN`:

```python
from pathlib import Path

from ..registry import PackagePlugin
from .renderer import SUPPORTED_PIN_COUNTS, SoicRenderer


PACKAGE_PLUGIN = PackagePlugin(
    family="SOIC",
    pin_counts=SUPPORTED_PIN_COUNTS,
    renderer_factory=SoicRenderer,
    sample_directory=Path(__file__).resolve().with_name("samples"),
)
```

This illustrates the declaration; SOIC is not currently implemented.

- `family` is a unique uppercase identifier, starting with a letter and using
  letters, digits, `_`, or `-` afterward.
- `pin_counts` is a nonempty, sorted tuple of unique positive integers. Derive it
  from package-owned variant data so another variant requires only a new asset.
- `renderer_factory` accepts a pin count and returns a fresh `IcRenderer` with
  that count and its reference measurements.
- `sample_directory` points to the new package's `samples` folder.

Discovery imports local package folders in deterministic order. Folders without
`plugin.py` are ignored; duplicate family IDs and invalid plugin exports produce
errors. JSON only selects an installed family by ID, never an import path.

No root export, registry entry, loader branch, or input-schema enum is needed.
The schema validates JSON structure; the discovered plugin validates supported
family/count combinations. Use the same input format for the new family:

```json
"package": {"family": "SOIC", "pin_count": 8}
```

Python callers can import the renderer from the new folder or call
`get_package("SOIC").create_renderer(8)` from
`components.renderer.packages.registry`.

### Supply annotation placement when needed

The default `pinout_factory` is `PinoutRenderer`, which supports left/right pins.
For another arrangement, such as four-sided pins, implement a `PinoutRenderer`
subclass inside the new package and pass it as `pinout_factory` in the plugin.
Its `render()` must accept the same name, definitions, orientation,
`content_scale`, and `pin_types` arguments and return a `SvgDocument`.

Keep layout-specific placement in that package. Continue to validate bounds,
preserve empty function-column slots, and reject overlaps or unreadable layouts.

### Package the assets

Python modules under `components` are discovered automatically. The packaging
configuration includes `samples/*.svg`, `variants/*.json`, and
`variant.schema.json` for every package. Following this layout requires no
packaging edits. Colocated test packages are excluded from distributions.
Additional asset formats or runtime dependencies must be
declared in `pyproject.toml`.

## Validate and regenerate samples

GitHub Actions runs the license-header check with `addlicense` v1.2.0 and the
complete test suite on Python 3.10 and 3.14 for every push and pull request.
The [CI workflow](.github/workflows/ci.yml) can also be run manually from the
Actions tab. It installs project dependencies with `python -m pip install .`.

Place component tests in that component's `tests/` folder, with an `__init__.py`
and `test_*.py` modules so `unittest` can discover them. For example, DIP geometry,
reference, and variant-validation tests belong in
`components/renderer/packages/dip/tests/`. Test fixtures belong with their owning
tests; the neutral input fixture is in `components/input/tests/fixtures/`.

Keep cross-component workflows, CLI tests, and package-extension integration
tests under `tests/integration/`. The root `tests/` package holds only integration
tests and its discovery initializer; component tests live beside their code.

Run commands from the repository root in the project environment:

```sh
python -m unittest discover -s . -t .
python -m components.renderer.packages.samples
```

Run just the integration tests with:

```sh
python -m unittest discover -s tests/integration -t .
```

Run one component's tests with its directory, for example:

```sh
python -m unittest discover -s components/renderer/packages/dip/tests -t .
```

The generator discovers every installed family and writes every supported count
in both orientations into that plugin's `samples/` folder. Generic samples use
`EXAMPLE` as the IC name. Concrete IC JSON, notes, render commands, and diagrams stay in `collection/`.

Run only the all-package sample tests with:

```sh
python -m unittest discover -s components/renderer/packages/tests -t .
```

The shared tests check complete sample generation, physical numbering, viewBox
dimensions, and byte-identical repeated output. Extension tests also verify a
new family supplied only as a new folder and a new DIP variant supplied only as
a new JSON asset in a fresh process.

Add package-specific tests for specification values, input constraints, pin-one
orientation, numbering, geometry bounds, and annotation placement. Visually
inspect representative SVGs in both orientations, including the smallest and
largest variants and dense labels; passing tests alone does not establish
readability. Include the generated samples, check for whitespace errors, and
follow [AGENTS.md](AGENTS.md) for Python documentation and style.
