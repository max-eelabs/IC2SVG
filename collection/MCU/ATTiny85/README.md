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

# ATtiny85 DIP-8 pinout

[JSON source](attiny85.json) · [Horizontal SVG](attiny85-horizontal.svg) ·
[Vertical SVG](attiny85-vertical.svg)

The diagram covers the native pin functions in Figure 1-1 and Table 10-3 of the
[Microchip/Atmel datasheet, revision 2586Q](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-2586-AVR-8-bit-Microcontroller-ATtiny25-ATtiny45-ATtiny85_Datasheet.pdf).
Related details are in Sections 10.3, 12, and 15.

- In JSON, prefix a signal with `~` to draw an overbar above that signal.
  The bar marks active-low reset or a complementary timer output; the tilde
  itself is not printed. In `OC0A/~OC1A`, only `OC1A` receives an overbar.
- `PB5*` shares RESET/debugWIRE. GPIO and PCINT5 require the appropriate reset
  fuse configuration. ADC0 also shares this pad; reset behavior must be considered.
- `DI`, `DO`, and `USCK` are USI three-wire signals. `MOSI`, `MISO`, and `SCK`
  are the ISP aliases shown in the pinout. For a USI SPI master, DO transmits
  MOSI and DI receives MISO; do not infer master wiring from the ISP aliases.
- SDA/SCL use USI two-wire mode with firmware support, rather than a standalone
  full I2C controller.
- There is no hardware DAC or dedicated UART. Filtered PWM can approximate
  analog output; UART needs software or a USI-assisted implementation. These
  options are not labeled as fixed native DAC/TX/RX pins.
- Alternate functions share pads and cannot all operate simultaneously.

Definitions use explicit columns, with blanks retained. Related signals share
boxes where needed. The saved render settings are:

| Orientation | Content scale | Legend |
| --- | --- | --- |
| Landscape | 35% | Automatic; 3 columns with at most 4 entries each |
| Portrait | 20% | 1 column, selected with `--legend-columns 1` |

The JSON uses `"legend_columns": null` for automatic layout. The portrait command
requests one column so the ten entries form a compact list without wrapping.
Descriptions stay on one line and use `...` when they exceed 24 characters or
the available width. Full category names remain in JSON. Headings and overlay
text retain their sheet sizes independently of the chip scale.

Regenerate both orientations, including the explanatory notes, with:

```powershell
.\render.cmd
```

Run this from the collection folder, or double-click `render.cmd` on Windows.
The command uses the repository virtual environment when available and otherwise
uses `python` from PATH. It reads this folder's JSON and replaces both SVGs.

The notes are stored in the JSON `comments` array and also appear when using
the generic JSON renderer, in a left-aligned block at the sheet's bottom left.
