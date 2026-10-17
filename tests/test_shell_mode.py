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


class TestShellMode(unittest.TestCase):
    def test_react_vite_shell_detected(self):
        html = '<!DOCTYPE html><html lang="en"><head><title>App</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "SHELL_ONLY")
        self.assertEqual(res["deterministic_score"], 100)  # Head rules clean
        self.assertLess(res["visible_text_chars"], 200)

    def test_nextjs_shell_detected(self):
        html = '<!DOCTYPE html><html lang="en"><head><title>Next App</title></head><body><div id="__next"></div><script src="/_next/static/chunks/main.js"></script></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "SHELL_ONLY")

    def test_vue_nuxt_shell_detected(self):
        html = '<!DOCTYPE html><html lang="en"><head><title>Nuxt</title></head><body><div id="__nuxt"></div><script src="/entry.js"></script></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "SHELL_ONLY")

    def test_tiny_static_page_without_scripts_is_full_mode(self):
        # A tiny static page with minimal text and no scripts should be audited in FULL mode
        html = '<!DOCTYPE html><html lang="en"><head><title>Tiny</title></head><body><main><h1>Hello World</h1><p>Static micro note.</p></main></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "FULL")
        self.assertEqual(res["script_tag_count"], 0)

    def test_page_with_scripts_and_substantial_text_is_full_mode(self):
        # Substantial text (>= 200 chars) with scripts must run in FULL mode
        content = "Accessible content block with extensive description explaining validator architecture and consensus proofs. " * 3
        html = f'<!DOCTYPE html><html lang="en"><head><title>Full App</title></head><body><main><h1>Header</h1><p>{content}</p><script src="/analytics.js"></script></main></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "FULL")
        self.assertGreaterEqual(res["visible_text_chars"], 200)
        self.assertEqual(res["script_tag_count"], 1)

    def test_shell_mode_evaluates_only_head_rules(self):
        # Even if body has unlabelled inputs or missing alts, SHELL_ONLY evaluates only R6, R7, R9
        html = '<html><head></head><body><div id="root"></div><script src="/app.js"></script><img src="x.png"><input type="text"></body></html>'
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "SHELL_ONLY")
        # Head rules: R6 (missing lang) and R7 (missing title) flagged
        self.assertEqual(res["rule_counts"]["R6"], 1)
        self.assertEqual(res["rule_counts"]["R7"], 1)
        # Body rules: R1, R3 NOT evaluated in SHELL_ONLY
        self.assertEqual(res["rule_counts"]["R1"], 0)
        self.assertEqual(res["rule_counts"]["R3"], 0)


if __name__ == "__main__":
    unittest.main()
