# Copyright 2026 Maxim Pavlov <pavlov.web@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Check sheet-anchored comments, wrapping, and interchangeable styles."""

from collections.abc import Sequence
from importlib.resources import files
import unittest
from xml.etree import ElementTree as ET

from PIL import ImageFont

from components.input import load_input
from components.renderer import (
    BottomLeftCommentsRenderer, CommentsRenderer, Rectangle, SvgDocument,
)


_SVG = "{http://www.w3.org/2000/svg}"


class CommentsTests(unittest.TestCase):
    """Validate bottom-left placement without centering or content transforms."""

    def test_bottom_left_alignment_and_scale_independence(self) -> None:
        for size in ((1920, 1080), (1080, 1920)):
            blocks = []
            for scale in (0.2, 0.6, 1.0):
                document = SvgDocument(size, content_scale=scale)
                bounds = BottomLeftCommentsRenderer().render(
                    document, ("First comment", "Second comment")
                )
                blocks.append(bounds)
                self.assertEqual(bounds.left, 32)
                self.assertEqual(bounds.bottom, size[1] - 32)
                root = ET.fromstring(document.to_string())
                comments = root.find(f"{_SVG}g[@id='comments']")
                self.assertEqual(comments.get("transform"), "translate(0 0) scale(1)")
                groups = comments.findall(f"{_SVG}g")
                self.assertEqual([g.get("aria-label") for g in groups],
                                 ["Comments", "First comment", "Second comment"])
                for group in groups:
                    first_glyph = group.find(f"{_SVG}path")
                    self.assertTrue(first_glyph.get("transform").startswith(
                        "translate(32 "
                    ))
                self.assertFalse(comments.findall(f"{_SVG}rect"))
            self.assertEqual(blocks[0], blocks[1])
            self.assertEqual(blocks[1], blocks[2])

    def test_wrapping_and_overflow(self) -> None:
        document = SvgDocument((1080, 1920))
        renderer = BottomLeftCommentsRenderer()
        renderer.render(document, ["Long comments wrap to the sheet. " * 20,
                                   "W" * 1000])
        root = ET.fromstring(document.to_string())
        comments = root.find(f"{_SVG}g[@id='comments']")
        lines = comments.findall(f"{_SVG}g")[1:]
        self.assertGreater(len(lines), 2)
        font = ImageFont.load_default(size=16)
        for line in lines:
            self.assertLessEqual(font.getlength(line.get("aria-label")), 1080 - 64)
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            renderer.render(document, ["line\n" * 100])
        with self.assertRaises(ValueError):
            renderer.render(document, ["   "])

    def test_json_comments_and_custom_style(self) -> None:
        class RecordingComments(CommentsRenderer):
            """Minimal independent implementation for composition verification."""

            def render(
                self, document: SvgDocument, comments: Sequence[str]
            ) -> Rectangle:
                self.received = tuple(comments)
                return Rectangle(32, 32, 32, 32)

        path = files("components.input").joinpath(
            "tests", "fixtures", "pinout-columns.json"
        )
        pinout = load_input(path)
        self.assertEqual(len(pinout.comments), 5)
        root = ET.fromstring(pinout.render().to_string())
        self.assertIsNotNone(root.find(f"{_SVG}g[@id='comments']"))
        custom = RecordingComments()
        pinout.render(comments_renderer=custom)
        self.assertEqual(custom.received, pinout.comments)
        with self.assertRaises(TypeError):
            CommentsRenderer()


if __name__ == "__main__":
    unittest.main()
