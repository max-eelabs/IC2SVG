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

# Python documentation and code style

These rules apply to project-owned Python code in this repository, including
application modules, scripts, and tests. Preserve existing behavior when changing
style. Do not reformat third-party code, generated files, or reference assets.

## Documentation

- Use `#` for single-line comments, including brief descriptions of constants,
  variables, and tables. Do not use standalone string literals as comments.
- Use triple-double-quoted docstrings for module overviews and public module,
  class, and function contracts. Start with a concise summary; add Google-style
  `Args:`, `Returns:`, `Raises:`, and `Notes:` sections where useful. Do not add
  empty sections or repeat information already clear from names and type hints.
- Document input constraints, units, coordinate conventions, mutable-data
  ownership, side effects, file access, and return-value meaning where relevant.
- Keep public API contracts in docstrings at their definitions and
  implementation-specific explanations beside the code.
- Explain intent and non-obvious constraints rather than narrating each statement.
  Keep comments and docstrings accurate when code changes.

## Code blocks and formatting

- Follow PEP 8 and PEP 257. Use four-space indentation, no tabs, and a default
  maximum line length of 88 characters unless project tooling specifies otherwise.
- Use `snake_case` for modules, functions, parameters, and variables; `PascalCase`
  for classes; and `UPPER_SNAKE_CASE` for constants. Preserve established public
  names and external data-format keys unless an API change is intended.
- Add type hints to new or changed function signatures. Prefer precise types
  over `Any`; do not add runtime complexity solely to satisfy annotations.
- Group related statements into logical blocks separated by one blank line.
  Separate setup, validation, layout work, rendering, and final returns when they
  form distinct steps. Keep tightly related operations together.
- Keep a block's introductory comment directly above its first statement;
  place the separating blank line before the comment, not after it.
- Separate top-level functions and classes with two blank lines and methods
  with one. Separate individually documented module-level declarations with
  a blank line. Do not insert blank lines between every statement.
- Avoid blank lines immediately inside function bodies and trailing whitespace.
- Keep imports explicit and at module scope unless there is a concrete reason
  to defer them. Group standard-library, third-party, and local imports in that
  order, with a blank line between groups. Do not use wildcard imports.
- Prefix module-private helpers and state with `_`. Prefer explicit arguments
  and return values over mutable module-level state. Avoid mutable default
  arguments and unexpected mutation of caller-owned data.
- Keep modules safe to import: parsing CLI arguments, writing files, and starting
  rendering belong in explicit entry points. Guard directly executable scripts
  with `if __name__ == "__main__":`.

## Early returns and errors

- If an entire function body, or its remaining useful work, is wrapped in an
  `if`, prefer an inverted guard followed by an early return. Leave the normal
  work at the function's outer indentation level.
- Separate the guard from the normal work with a blank line. Do not add an
  `else` after a branch that returns or raises.
- Preserve short-circuit evaluation, return values, and required cleanup. Use
  context managers or `try`/`finally` for resource cleanup when appropriate.
- Raise specific exceptions with actionable messages for invalid input or failed
  operations. Do not use assertions for user-input validation or silently suppress
  exceptions. Translate expected errors into concise messages at the CLI boundary.

```python
def render_if_ready(request: RenderRequest) -> None:
    if not request.ready:
        return

    layout = prepare_layout(request)
    write_image(layout, request.output_path)
```

## Deterministic rendering

- Keep input validation, package geometry, layout, and image rendering separate.
  Physical pin numbers, alternate functions, categories, and board aliases must
  retain their distinct meanings.
- Make pin, label, and legend ordering explicit. Preserve meaningful input order
  and use documented sorting rules elsewhere; never depend on set iteration order.
- Use fixed fonts and defined layout parameters. Avoid random placement,
  timestamps, network lookups, and implicit system-font substitution in output.
- Use SVG as the only output, with a fixed logical viewBox of 1920 x 1080
  for landscape or 1080 x 1920 for portrait. Scale viewport dimensions uniformly
  so geometry, strokes, and font outlines retain their proportions.
  Report unsupported packages and layouts
  that cannot fit legibly; do not silently omit definitions or clip labels.
- Keep defaults and color overrides in a clear configuration layer. Validate
  inputs before rendering rather than scattering fallback behavior through
  drawing functions.

## Project integration and validation

- Register new modules, package assets, dependencies, and CLI entry points in
  the project's packaging configuration when it exists. Keep tool configuration
  in `pyproject.toml` where supported; do not edit generated environment files.
- Declare runtime and development dependencies explicitly. Follow the project's
  Python-version constraints and dependency-locking workflow when established.
- Run configured formatting, linting, type checks, and relevant tests after
  code or control-flow changes. Do not claim checks ran if tooling is not yet
  configured; report what was verified and any remaining limitations.
- Add meaningful tests for changed behavior, especially input validation, pin
  numbering, layout bounds, orientation sizes, color overrides, and repeated
  rendering with identical inputs. Avoid tests that merely mirror implementation.
- Visually inspect representative images after layout or typography changes.
  Report visual inspection separately from automated checks; passing tests alone
  does not establish that labels are readable or correctly arranged.
- Check the diff for whitespace errors. Keep README examples and usage
  instructions consistent with the implemented behavior.
