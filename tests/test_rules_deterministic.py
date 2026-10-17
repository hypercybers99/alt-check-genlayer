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

from AltCheck import _evaluate_deterministic_rules


class TestRulesDeterministic(unittest.TestCase):
    # R1: Images without alt
    def test_r1_missing_alt(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="test.jpg"></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R1"], 1)
        self.assertEqual(len(res["snippets"]["R1"]), 1)
        self.assertIn(res["snippets"]["R1"][0], html)

    def test_r1_decorative_presentation_allowed(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="decor.png" alt="" role="presentation"><img src="none.png" alt="" role="none"><img src="hidden.png" alt="" aria-hidden="true"></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R1"], 0)
        self.assertEqual(res["decorative_unmarked"], 0)

    def test_r1_decorative_unmarked_info(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="unmarked.png" alt=""></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R1"], 0)
        self.assertEqual(res["decorative_unmarked"], 1)

    def test_r1_cap_at_8(self):
        imgs = "".join(f'<img src="img{i}.png">' for i in range(12))
        html = f'<main lang="en"><h1>Title</h1><title>T</title>{imgs}</main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R1"], 12)  # Raw count is 12, capped at 8 in score deductions
        self.assertLessEqual(len(res["snippets"]["R1"]), 5)

    # R2: Poor alt text
    def test_r2_filename_like_alt(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="1.png" alt="chart.png"><img src="2.jpg" alt="IMG_1024.JPG"></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R2"], 2)

    def test_r2_generic_word_alt(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="1.png" alt="photo"><img src="2.jpg" alt="hinh anh"></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R2"], 2)

    def test_r2_descriptive_alt_clean(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><img src="1.png" alt="Architectural diagram of consensus validator pipeline"></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R2"], 0)

    # R3: Form controls
    def test_r3_controls_without_name(self):
        html = '<main lang="en"><h1>Title</h1><title>T</title><input type="text"><select><option>Opt</option></select><textarea></textarea></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R3"], 3)

    def test_r3_controls_with_name_clean(self):
        html = (
            '<main lang="en"><h1>Title</h1><title>T</title>'
            '<label for="i1">Name</label><input id="i1" type="text">'
            '<select aria-label="Role"><option>A</option></select>'
            '<textarea title="Comments"></textarea>'
            '<input type="hidden" name="csrf">'
            '<input type="submit" value="Send">'
            '</main>'
        )
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R3"], 0)

    # R4: Links & buttons
    def test_r4_generic_phrases(self):
        html = (
            '<main lang="en"><h1>Title</h1><title>T</title>'
            '<a href="/1">click here</a>'
            '<a href="/2">read more...</a>'
            '<a href="/3">bam vao day</a>'
            '<a href="/4"></a>'
            '<button type="button"></button>'
            '</main>'
        )
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R4"], 5)

    def test_r4_descriptive_links_clean(self):
        html = (
            '<main lang="en"><h1>Title</h1><title>T</title>'
            '<a href="/audit">Download comprehensive security report 2026</a>'
            '<button type="button">Deploy Smart Contract</button>'
            '</main>'
        )
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R4"], 0)

    # R5: Heading structure
    def test_r5_missing_h1(self):
        html = '<main lang="en"><title>T</title><h2>Subtitle</h2><p>Content</p></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R5"], 1)

    def test_r5_multiple_h1(self):
        html = '<main lang="en"><title>T</title><h1>Main 1</h1><h1>Main 2</h1></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R5"], 1)

    def test_r5_skipped_heading_level(self):
        html = '<main lang="en"><title>T</title><h1>Main</h1><h3>Skipped to 3</h3></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R5"], 1)

    def test_r5_sequential_headings_clean(self):
        html = '<main lang="en"><title>T</title><h1>Main</h1><h2>Section</h2><h3>Sub</h3></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R5"], 0)

    # R6: <html lang>
    def test_r6_missing_html_lang(self):
        html = '<html><head><title>T</title></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R6"], 1)

    def test_r6_empty_html_lang(self):
        html = '<html lang="   "><head><title>T</title></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R6"], 1)

    def test_r6_valid_html_lang(self):
        html = '<html lang="en"><head><title>T</title></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R6"], 0)

    # R7: <title>
    def test_r7_missing_title(self):
        html = '<html lang="en"><head></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R7"], 1)

    def test_r7_empty_title(self):
        html = '<html lang="en"><head><title>   </title></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R7"], 1)

    def test_r7_valid_title(self):
        html = '<html lang="en"><head><title>Accessible Demo</title></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R7"], 0)

    # R8: Duplicate IDs
    def test_r8_duplicate_ids(self):
        html = '<main lang="en"><title>T</title><h1>Title</h1><div id="dup">A</div><div id="dup">B</div><span id="uniq">C</span></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R8"], 1)

    # R9: Viewport meta zoom
    def test_r9_zoom_disabled_user_scalable_no(self):
        html = '<html lang="en"><head><title>T</title><meta name="viewport" content="width=device-width, user-scalable=no"></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R9"], 1)

    def test_r9_zoom_disabled_max_scale_under_2(self):
        html = '<html lang="en"><head><title>T</title><meta name="viewport" content="width=device-width, maximum-scale=1.0"></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R9"], 1)

    def test_r9_zoom_enabled_clean(self):
        html = '<html lang="en"><head><title>T</title><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0"></head><main><h1>Title</h1></main></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R9"], 0)

    # R10: Positive tabindex
    def test_r10_positive_tabindex(self):
        html = '<main lang="en"><title>T</title><h1>Title</h1><div tabindex="1"></div><div tabindex="2"></div><div tabindex="0"></div><div tabindex="-1"></div></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R10"], 2)

    # R11: Main landmark
    def test_r11_missing_main(self):
        html = '<html lang="en"><head><title>T</title></head><body><h1>Title</h1><div>No main</div></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R11"], 1)

    def test_r11_role_main_counts_as_main(self):
        html = '<html lang="en"><head><title>T</title></head><body><div role="main"><h1>Title</h1></div></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R11"], 0)

    # R12: iframe without title
    def test_r12_iframe_missing_title(self):
        html = '<main lang="en"><title>T</title><h1>Title</h1><iframe src="test.html"></iframe></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R12"], 1)

    def test_r12_iframe_with_title_clean(self):
        html = '<main lang="en"><title>T</title><h1>Title</h1><iframe src="test.html" title="Interactive map"></iframe></main>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["rule_counts"]["R12"], 0)


if __name__ == "__main__":
    unittest.main()
