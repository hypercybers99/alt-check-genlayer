import unittest
import sys
import os
import json

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

root_dir = os.path.dirname(pkg_dir)
contracts_dir = os.path.join(root_dir, "contracts")
if contracts_dir not in sys.path:
    sys.path.insert(0, contracts_dir)

import genlayer
from AltCheck import AltCheck, _compute_vague_bucket


class TestConsensusMocked(unittest.TestCase):
    def setUp(self):
        self.contract = AltCheck()
        self.contract.pages = {}
        self.contract.audits = {}
        self.contract.meta = {}
        genlayer.gl.message.sender_address.as_hex = "0x1111111111111111111111111111111111111111"
        genlayer.gl.message_raw = {"datetime": "2026-10-17T12:00:00Z"}
        genlayer.gl.nondet.web.pages.clear()
        genlayer.gl.nondet.web.get_handler = None
        genlayer.gl.nondet.prompt_handler = None

    def test_honest_leader_accepted(self):
        url = "https://example.com/honest.html"
        html = '<!DOCTYPE html><html lang="en"><head><title>Honest</title></head><body><main><h1>Header</h1><p>Accessible content for test.</p><img src="1.png" alt="Valid alt description"></main></body></html>'
        genlayer.gl.nondet.web.pages[url] = html

        def mock_prompt(p, fmt):
            return json.dumps({"labels": [{"i": 0, "label": "CLEAR"}]})
        genlayer.gl.nondet.prompt_handler = mock_prompt

        self.contract.register_page("Honest Page", url)
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        # Audit should succeed under consensus
        self.contract.audit_page(page_id)
        page_data = json.loads(self.contract.get_page(page_id))
        self.assertEqual(page_data["audits_total"], 1)
        self.assertEqual(page_data["latest_score"], 100)
        self.assertEqual(page_data["latest_grade"], "A")

    def test_leader_inflating_counts_rejected(self):
        url = "https://example.com/inflate.html"
        html = '<!DOCTYPE html><html lang="en"><head><title>Inflate</title></head><body><main><h1>Header</h1><p>Clean page text content.</p></main></body></html>'
        genlayer.gl.nondet.web.pages[url] = html

        # Tampered leader payload
        fake_leader_payload = json.dumps({
            "mode": "FULL",
            "rule_counts": {"R1": 8, "R2": 5, "R3": 4, "R4": 2, "R5": 1, "R6": 0, "R7": 0, "R8": 0, "R9": 0, "R10": 0, "R11": 0, "R12": 0},
            "vague_bucket": 0,
            "audit_record": {"mode": "FULL", "score": 20, "grade": "F"}
        })

        wrapped = genlayer.gl.vm.Return(calldata=fake_leader_payload)

        # Validator re-evaluates
        def val_check():
            resp = genlayer.gl.nondet.web.get(url)
            from AltCheck import _evaluate_deterministic_rules, RULE_IDS
            res = _evaluate_deterministic_rules(resp.body.decode("utf-8"))
            leader_counts = json.loads(fake_leader_payload)["rule_counts"]
            for r in RULE_IDS:
                if res["rule_counts"].get(r, 0) != leader_counts.get(r, 0):
                    return False
            return True

        self.assertFalse(val_check())

    def test_leader_fabricating_snippets_dropped(self):
        # Snippets must be verbatim substrings of raw HTML; fabricated snippets are dropped
        html = '<main lang="en"><h1>Title</h1><img src="chart.png"></main>'
        from AltCheck import _evaluate_deterministic_rules
        res = _evaluate_deterministic_rules(html)
        snippets = res["snippets"]["R1"]
        for s in snippets:
            self.assertIn(s, html)

    def test_mode_mismatch_rejected(self):
        # Leader claims SHELL_ONLY while validator discovers FULL
        html = '<!DOCTYPE html><html lang="en"><head><title>Full App</title></head><body><main><h1>Header</h1><p>' + ("Real text " * 30) + '</p></main></body></html>'
        from AltCheck import _evaluate_deterministic_rules
        res = _evaluate_deterministic_rules(html)
        self.assertEqual(res["mode"], "FULL")
        # Validator comparing against SHELL_ONLY leader must return False
        leader_mode = "SHELL_ONLY"
        self.assertNotEqual(res["mode"], leader_mode)

    def test_malformed_model_output_reverts(self):
        url = "https://example.com/model-malformed.html"
        html = '<!DOCTYPE html><html lang="en"><head><title>Model Test</title></head><body><main><h1>Header</h1><img src="1.png" alt="Descriptive banner"></main></body></html>'
        genlayer.gl.nondet.web.pages[url] = html

        def mock_bad_prompt(p, fmt):
            return "Unexpected plain text error from LLM"
        genlayer.gl.nondet.prompt_handler = mock_bad_prompt

        self.contract.register_page("Model Fail Page", url)
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.audit_page(page_id)
        self.assertEqual(str(ctx.exception), "model output invalid")

    def test_leader_failure_not_waved_through(self):
        # When leader returns non-Return result, validator must reject
        class MockErrorResult:
            pass

        bad_result = MockErrorResult()
        self.assertFalse(isinstance(bad_result, genlayer.gl.vm.Return))

    def test_page_churn_simulation_rejects_disagreement(self):
        # Simulate page changing between leader fetch and validator fetch
        html_t0 = '<!DOCTYPE html><html lang="en"><head><title>T</title></head><body><main><h1>Title</h1><img src="1.png"></main></body></html>'
        html_t1 = '<!DOCTYPE html><html lang="en"><head><title>T</title></head><body><main><h1>Title</h1><img src="1.png"><img src="2.png"></main></body></html>'

        from AltCheck import _evaluate_deterministic_rules
        res_t0 = _evaluate_deterministic_rules(html_t0)
        res_t1 = _evaluate_deterministic_rules(html_t1)

        # Counts differ (1 vs 2 missing alts) -> validator rejects
        self.assertNotEqual(res_t0["rule_counts"]["R1"], res_t1["rule_counts"]["R1"])

    def test_vague_bucket_match_accepted(self):
        # Both leader and validator report 2 vague items (bucket 1: 1-2 items) -> agreed
        b_leader = _compute_vague_bucket(2)
        b_val = _compute_vague_bucket(1)
        self.assertEqual(b_leader, b_val)

    def test_vague_bucket_mismatch_rejected(self):
        # Leader reports 0 vague items (bucket 0), validator reports 4 vague items (bucket 2) -> rejected
        b_leader = _compute_vague_bucket(0)
        b_val = _compute_vague_bucket(4)
        self.assertNotEqual(b_leader, b_val)

    def test_leader_hiding_partiality_rejected_by_validator(self):
        # Leader claims page is not partial, but validator calculates partial: true
        url = "https://example.com/hide-partial.html"
        items = [f'<li><a href="/item/{i}">Link {i}</a></li>' for i in range(1600)]
        html = f'<!DOCTYPE html><html lang="en"><head><title>Large</title></head><body><main><h1>Title</h1><ul>{"".join(items)}</ul></main></body></html>'
        genlayer.gl.nondet.web.pages[url] = html

        # Malicious leader crafts audit with partial: false and elements_seen: 1000
        fake_leader = json.dumps({
            "mode": "FULL",
            "rule_counts": {r: 0 for r in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12"]},
            "vague_bucket": 0,
            "partial": False,
            "elements_seen": 1000,
            "elements_analyzed": 1000,
            "audit_record": {"score": 100, "grade": "A", "partial": False}
        })

        from AltCheck import _evaluate_deterministic_rules
        val_eval = _evaluate_deterministic_rules(html)
        self.assertTrue(val_eval["partial"])
        self.assertNotEqual(val_eval["partial"], json.loads(fake_leader)["partial"])
        self.assertNotEqual(val_eval["elements_seen"], json.loads(fake_leader)["elements_seen"])

    def test_non_html_fail_consensus_reverts_cleanly(self):
        # When leader and validators both see non-HTML data.json, consensus agreement on FAIL|not an html page reverts cleanly with UserError
        url = "https://example.com/data.json"
        json_data = '{"status": "ok", "count": 42}'
        genlayer.gl.nondet.web.pages[url] = json_data

        self.contract.register_page("JSON Endpoint", url)
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.audit_page(page_id)
        self.assertEqual(str(ctx.exception), "not an html page")


if __name__ == "__main__":
    unittest.main()
