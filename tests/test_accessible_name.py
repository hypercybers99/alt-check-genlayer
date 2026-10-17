import unittest
import sys
import os

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

root_dir = os.path.dirname(pkg_dir)
contracts_dir = os.path.join(root_dir, "contracts")
if contracts_dir not in sys.path:
    sys.path.insert(0, contracts_dir)

from AltCheck import DOMParser, _compute_accessible_name


class TestAccessibleName(unittest.TestCase):
    def test_priority_1_aria_labelledby_over_aria_label(self):
        raw = '<div id="lbl">Referenced Header</div><button aria-labelledby="lbl" aria-label="Fallback Label" title="Title">Ignored Text</button>'
        parser = DOMParser(raw)
        parser.feed(raw)
        btn = parser.elements[1]
        name = _compute_accessible_name(btn, parser)
        self.assertEqual(name, "Referenced Header")

    def test_priority_2_aria_label_over_for_label(self):
        raw = '<label for="inp">Field Label</label><input id="inp" type="text" aria-label="Explicit Aria" title="Field Title">'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[1]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "Explicit Aria")

    def test_priority_3_for_label_over_wrapping_label(self):
        raw = '<label for="inp">Specific Target</label><label>Wrapping Container <input id="inp" type="text"></label>'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[2]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "Specific Target")

    def test_priority_4_wrapping_label(self):
        raw = '<label>Billing Address <input type="text" name="address"></label>'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[1]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "Billing Address")

    def test_priority_5_title_attribute(self):
        raw = '<input type="text" title="Enter search term" name="q">'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[0]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "Enter search term")

    def test_priority_6_visible_text(self):
        raw = '<a href="/dashboard">Account Overview</a>'
        parser = DOMParser(raw)
        parser.feed(raw)
        a = parser.elements[0]
        name = _compute_accessible_name(a, parser)
        self.assertEqual(name, "Account Overview")

    def test_priority_7_input_submit_value(self):
        raw = '<input type="submit" value="Save Changes">'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[0]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "Save Changes")

    def test_aria_labelledby_with_multiple_and_missing_ids(self):
        raw = '<span id="part1">First</span><span id="part2">Second</span><button aria-labelledby="part1 missing_id part2">Button</button>'
        parser = DOMParser(raw)
        parser.feed(raw)
        btn = parser.elements[2]
        name = _compute_accessible_name(btn, parser)
        self.assertEqual(name, "First Second")

    def test_placeholder_alone_does_not_count(self):
        raw = '<input type="text" placeholder="Type here without label">'
        parser = DOMParser(raw)
        parser.feed(raw)
        inp = parser.elements[0]
        name = _compute_accessible_name(inp, parser)
        self.assertEqual(name, "")

    def test_nested_image_alt_in_link(self):
        raw = '<a href="/home"><img src="home.png" alt="Homepage Gateway"></a>'
        parser = DOMParser(raw)
        parser.feed(raw)
        a = parser.elements[0]
        name = _compute_accessible_name(a, parser)
        self.assertEqual(name, "Homepage Gateway")

    def test_punctuation_only_name_counts_as_empty(self):
        raw = '<button type="button"> &gt;&gt;&gt; </button>'
        parser = DOMParser(raw)
        parser.feed(raw)
        btn = parser.elements[0]
        name = _compute_accessible_name(btn, parser)
        self.assertEqual(name, "")

    def test_whitespace_collapsing(self):
        raw = '<button type="button">  Multi \n\t line   spaced   text  </button>'
        parser = DOMParser(raw)
        parser.feed(raw)
        btn = parser.elements[0]
        name = _compute_accessible_name(btn, parser)
        self.assertEqual(name, "Multi line spaced text")


if __name__ == "__main__":
    unittest.main()
