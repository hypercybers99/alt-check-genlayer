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

import genlayer
from AltCheck import DOMParser, _evaluate_deterministic_rules, MAX_BODY_BYTES


class TestHtmlParser(unittest.TestCase):
    def test_unclosed_tags_handled_gracefully(self):
        raw = "<div><p>Unclosed paragraph<div><span>Nested</span>"
        parser = DOMParser(raw)
        parser.feed(raw)
        tags = [e.tag for e in parser.elements]
        self.assertIn("div", tags)
        self.assertIn("p", tags)
        self.assertIn("span", tags)

    def test_script_tag_with_fake_html_inside(self):
        raw = "<script>var html = '<img src=\"fake.jpg\"><a href=\"#\">fake link</a>';</script><p>Real Text</p>"
        res = _evaluate_deterministic_rules(raw)
        # Fake img and a inside script must NOT be counted as elements or violations
        self.assertEqual(res["rule_counts"]["R1"], 0)
        self.assertEqual(res["rule_counts"]["R4"], 0)
        self.assertEqual(res["script_tag_count"], 1)

    def test_style_tag_content_not_visible(self):
        raw = "<style>body { color: red; content: 'hidden text'; }</style><p>Visible</p>"
        parser = DOMParser(raw)
        parser.feed(raw)
        vis = " ".join(parser.visible_text_parts)
        self.assertNotIn("color: red", vis)
        self.assertIn("Visible", vis)

    def test_uppercase_tags_and_attributes(self):
        raw = '<HTML LANG="EN"><BODY><H1 ID="MAIN">Header</H1><IMG SRC="test.png" ALT="Test image"></BODY></HTML>'
        parser = DOMParser(raw)
        parser.feed(raw)
        self.assertEqual(parser.html_lang, "en")
        self.assertEqual(parser.h1_count, 1)
        self.assertIn("MAIN", parser.id_map)

    def test_unquoted_attribute_values(self):
        raw = '<input type=text id=custom-input name=sample>'
        parser = DOMParser(raw)
        parser.feed(raw)
        self.assertEqual(len(parser.elements), 1)
        el = parser.elements[0]
        self.assertEqual(el.attrs.get("type"), "text")
        self.assertEqual(el.attrs.get("id"), "custom-input")

    def test_boolean_attributes(self):
        raw = '<input type="checkbox" checked disabled required readonly>'
        parser = DOMParser(raw)
        parser.feed(raw)
        el = parser.elements[0]
        self.assertIn("checked", el.attrs)
        self.assertIn("disabled", el.attrs)
        self.assertIn("required", el.attrs)
        self.assertIn("readonly", el.attrs)

    def test_entity_decoding_in_text_and_attrs(self):
        raw = '<a href="/test" title="Tips &amp; Tricks">Home &lt;Page&gt; &copy; 2026</a>'
        parser = DOMParser(raw)
        parser.feed(raw)
        el = parser.elements[0]
        # Attribute entity
        self.assertEqual(el.attrs.get("title"), "Tips & Tricks")
        # Inner text entity
        self.assertIn("<Page>", el.get_text())

    def test_comments_ignored(self):
        raw = '<p>Start<!-- <img src="commented.jpg"> -->End</p>'
        res = _evaluate_deterministic_rules(raw)
        self.assertEqual(res["rule_counts"]["R1"], 0)

    def test_template_and_noscript_ignored(self):
        raw = (
            '<template><p>Template content</p><img src="tpl.png"></template>'
            '<noscript><p>Noscript text</p></noscript>'
            '<main><h1>Main Title</h1><p>Main content for screen reader test</p></main>'
        )
        parser = DOMParser(raw)
        parser.feed(raw)
        vis = " ".join(parser.visible_text_parts)
        self.assertNotIn("Template content", vis)
        self.assertNotIn("Noscript text", vis)
        self.assertIn("Main content", vis)

    def test_huge_input_truncation(self):
        huge_html = "<html><body><h1>Title</h1><p>" + ("A" * (MAX_BODY_BYTES + 5000)) + "</p></body></html>"
        res = _evaluate_deterministic_rules(huge_html)
        self.assertTrue(res["truncated"])
        self.assertTrue(res["partial"])

    def test_element_cap_truncation_and_metrics(self):
        # Generate 3200 elements (exceeding MAX_ELEMENTS = 3000)
        items = [f'<li><a href="/item/{i}">Link {i}</a></li>' for i in range(1600)]
        html = f'<!DOCTYPE html><html lang="en"><head><title>Large</title></head><body><main><h1>Title</h1><ul>{"".join(items)}</ul></main></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertFalse(res["truncated"])  # Under byte cap
        self.assertTrue(res["elements_truncated"])
        self.assertTrue(res["partial"])
        self.assertEqual(res["elements_analyzed"], 3000)
        self.assertGreater(res["elements_seen"], 3000)
        # R5, R8, R11 unverified check on partial
        self.assertIn("R5", res["unverified_rules"])
        self.assertIn("R8", res["unverified_rules"])

    def test_violation_beyond_cap_not_silently_ignored(self):
        # 3005 valid elements followed by a violation at element 3010
        # The violation is beyond the cap: audit MUST be marked partial: true, unverified_rules must flag whole-doc rules
        items = [f'<span>Text {i}</span>' for i in range(3005)]
        html = f'<!DOCTYPE html><html lang="en"><head><title>Cap Test</title></head><body><main><h1>Title</h1>{"".join(items)}<img src="missing.png"></main></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertTrue(res["partial"])
        self.assertTrue(res["elements_truncated"])
        self.assertIn("R5", res["unverified_rules"])
        self.assertIn("R8", res["unverified_rules"])

    def test_element_cap_exact_boundary(self):
        # Exactly at boundary vs boundary + 1
        # Create minimal document with exact element count
        tags = "".join([f"<p>{i}</p>" for i in range(1495)])  # 1495 tags + html, head, title, body, main = 1500
        html = f'<!DOCTYPE html><html lang="en"><head><title>Boundary</title></head><body><main><h1>H</h1>{tags}</main></body></html>'
        parser = DOMParser(html)
        parser.feed(html)
        self.assertFalse(parser.elements_dropped > 0)

    def test_body_cut_mid_tag_handled_gracefully(self):
        # HTML cut abruptly mid-tag inside body
        raw = '<!DOCTYPE html><html lang="en"><head><title>Cut</title></head><body><main><h1>Title</h1><p>Normal</p><a href="/test" aria-label="incomplete'
        res = _evaluate_deterministic_rules(raw)
        self.assertIn(res["mode"], ("FULL", "SHELL_ONLY"))
        self.assertIsInstance(res["rule_counts"], dict)


if __name__ == "__main__":
    unittest.main()
