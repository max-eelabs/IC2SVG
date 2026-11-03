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

# PIC16F1454 PDIP-14 pinout

[JSON source](pic16f1454.json) · [Horizontal SVG](pic16f1454-horizontal.svg) ·
[Vertical SVG](pic16f1454-vertical.svg)

This entry covers the 14-pin PDIP package, viewed from above, with pin 1 beside
the housing notch. Physical numbering follows Figure 1 (page 3), and native
functions follow Table 1 (page 5) and Table 1-2 (pages 12-13) of the
[Microchip datasheet, revision DS40001639C](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/PIC16LF1454-5-9-14-20-Pin-8-Bit-Flash-USB-Microcontroller-with-XLP-Technology-DS40001639C.pdf).
The drawing uses the repository's illustrative DIP-14 geometry.

- A trailing `*` marks an alternate location selected with APFCON. Default/alternate
  pairs are T1G on RA4/RA3, PWM2 on RC3/RA5, SDO on RC2/RA4, SS on RC3/RA3,
  and CLKR on RA4/RC3. See the allocation-table notes and Section 12.2.
- RA0, RA1, and RA3 are input-only in GPIO mode and have IN badges. These badges
  describe GPIO direction; the USB D- and D+ functions on pins 12 and 13 remain
  bidirectional.
- RA3 shares active-low MCLR and programming voltage VPP. GPIO requires both
  MCLRE=0 and LVP=0; see Section 6.5. Prefixing a signal with `~` in JSON draws
  its active-low overbar, including SS.
- RC0/RC1 provide ICSPDAT/ICSPCLK. The additional programming functions on
  RA0/RA1 are for legacy PIC18(L)F1XK50 low-voltage programming support, as
  identified by Figure 1 note 1 and Table 1 note 3.
- VUSB3V3 is the USB regulator connection. Follow the USB power and decoupling
  requirements in the datasheet for the selected supply mode.
- The PIC16F1454 has no ADC, DAC, comparators, or CWG. Functions belonging only
  to the PIC16F1455/1459 are excluded (Table 1-1, page 10).
- Alternate functions share pads and cannot all operate simultaneously. EUSART
  TX/CK and RX/DT are asynchronous/synchronous mode alternatives; MSSP SPI and
  I2C also share pins. IOC denotes interrupt-on-change on PORTA.

For compact labels, `SI`/`SO` mean `SOSCI`/`SOSCO`, `OSC1/IN` means
`OSC1/CLKIN`, and `OSC2/OUT` means `OSC2/CLKOUT`. The legacy programming
labels `CLK(LVP)` and `DAT(LVP)` mean `ICSPCLK (LVP)` and `ICSPDAT (LVP)`.
An abbreviation key also appears in the diagram comments.

Function columns retain empty slots. The saved render settings are:

| Orientation | Content scale | Legend |
| --- | --- | --- |
| Landscape | 33.95% | Automatic; 3 columns with at most 4 entries each |
| Portrait | 14% | 2 columns, selected with `--legend-columns 2` |

The JSON uses `"legend_columns": null` for automatic layout. The portrait command
overrides it without changing the source. Headings and overlay text retain their
sheet sizes when the chip scale changes. Legend descriptions stay on one line
and use `...` when shortened; the full categories remain in JSON. The notes and
abbreviation key in `comments` appear on both diagrams.

Regenerate both SVGs from this directory, or double-click `render.cmd`:

```powershell
.\render.cmd
```

The command works from other directories, uses the repository's `.venv` Python
when available, and otherwise uses `python` from PATH. Both SVGs come from the
same JSON; the portrait scale and legend overrides are stored in `render.cmd`.
