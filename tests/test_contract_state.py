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
from AltCheck import AltCheck


class TestContractState(unittest.TestCase):
    def setUp(self):
        self.contract = AltCheck()
        self.contract.pages = {}
        self.contract.audits = {}
        self.contract.meta = {}
        genlayer.gl.message.sender_address.as_hex = "0x1111111111111111111111111111111111111111"
        genlayer.gl.message_raw = {"datetime": "2026-10-17T12:00:00Z"}

    # Registration tests
    def test_register_page_success(self):
        self.contract.register_page("Demo Site", "https://example.com/index.html")
        meta = json.loads(self.contract.get_meta())
        self.assertEqual(meta["pages_count"], 1)

        ids = json.loads(self.contract.list_page_ids(0, 10))
        self.assertEqual(len(ids), 1)
        page_id = ids[0]

        page_data = json.loads(self.contract.get_page(page_id))
        self.assertEqual(page_data["label"], "Demo Site")
        self.assertEqual(page_data["url"], "https://example.com/index.html")
        self.assertEqual(page_data["registrant"], "0x1111111111111111111111111111111111111111")
        self.assertEqual(page_data["audits_total"], 0)
        self.assertFalse(page_data["retired"])

    def test_register_page_duplicate_rejection(self):
        self.contract.register_page("Demo Site", "https://example.com/index.html")
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.register_page("Duplicate Demo", "https://example.com/index.html")
        self.assertEqual(str(ctx.exception), "page already registered")

    def test_register_page_label_bounds(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.register_page("ab", "https://example.com/path")
        self.assertEqual(str(ctx.exception), "invalid label length")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.register_page("x" * 81, "https://example.com/path")
        self.assertEqual(str(ctx.exception), "invalid label length")

    # Maintainer notes
    def test_add_maintainer_note_success(self):
        self.contract.register_page("Demo Site", "https://example.com/path")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        # Seed mock audit 1
        self.contract.audits[f"{page_id}:1"] = json.dumps({
            "page_id": page_id, "n": 1, "score": 90, "grade": "A", "notes": []
        })

        self.contract.add_maintainer_note(page_id, 1, "Remediated missing alt attributes")
        audit_raw = self.contract.audits[f"{page_id}:1"]
        audit = json.loads(audit_raw)
        self.assertEqual(len(audit["notes"]), 1)
        self.assertEqual(audit["notes"][0]["note"], "Remediated missing alt attributes")

    def test_add_maintainer_note_non_registrant_rejection(self):
        self.contract.register_page("Demo Site", "https://example.com/path")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]
        self.contract.audits[f"{page_id}:1"] = json.dumps({"notes": []})

        # Switch sender
        genlayer.gl.message.sender_address.as_hex = "0x2222222222222222222222222222222222222222"
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.add_maintainer_note(page_id, 1, "Attempt unauthorized note")
        self.assertEqual(str(ctx.exception), "only the registrant can do this")

    def test_add_maintainer_note_length_bounds(self):
        self.contract.register_page("Demo Site", "https://example.com/path")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]
        self.contract.audits[f"{page_id}:1"] = json.dumps({"notes": []})

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.add_maintainer_note(page_id, 1, "four")
        self.assertEqual(str(ctx.exception), "note length out of range")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.add_maintainer_note(page_id, 1, "x" * 281)
        self.assertEqual(str(ctx.exception), "note length out of range")

    def test_add_maintainer_note_cap_at_3(self):
        self.contract.register_page("Demo Site", "https://example.com/path")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]
        self.contract.audits[f"{page_id}:1"] = json.dumps({"notes": []})

        self.contract.add_maintainer_note(page_id, 1, "Note number one")
        self.contract.add_maintainer_note(page_id, 1, "Note number two")
        self.contract.add_maintainer_note(page_id, 1, "Note number three")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.add_maintainer_note(page_id, 1, "Excess note four")
        self.assertEqual(str(ctx.exception), "note limit reached for this audit")

    # Retirement
    def test_retire_page_success_and_exclusion(self):
        self.contract.register_page("Retirable Site", "https://example.com/retire")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        # Seed in best board
        self.contract.meta["board_best"] = json.dumps([{"id": page_id, "score": 95}])

        self.contract.retire_page(page_id)
        page_data = json.loads(self.contract.get_page(page_id))
        self.assertTrue(page_data["retired"])

        # Excluded from board
        board = json.loads(self.contract.get_board(10))
        self.assertEqual(len(board["best"]), 0)

        # Subsequent audit attempt fails
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.audit_page(page_id)
        self.assertEqual(str(ctx.exception), "page is retired")

    def test_retire_page_non_registrant_rejection(self):
        self.contract.register_page("Site", "https://example.com/site")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        genlayer.gl.message.sender_address.as_hex = "0x9999999999999999999999999999999999999999"
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.retire_page(page_id)
        self.assertEqual(str(ctx.exception), "only the registrant can do this")

    # Cooldown & Cap
    def test_audit_page_cooldown_active(self):
        self.contract.register_page("Cooldown Site", "https://example.com/cooldown")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        # Seed page with recent audit timestamp (only 60s ago, cooldown is 300s)
        from AltCheck import _get_current_timestamp
        now_ts, _ = _get_current_timestamp()
        page = json.loads(self.contract.get_page(page_id))
        page["last_audit_ts"] = now_ts - 60
        self.contract.pages[page_id] = json.dumps(page)

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.audit_page(page_id)
        self.assertEqual(str(ctx.exception), "audit cooldown active")

    def test_audit_page_max_cap_reached(self):
        self.contract.register_page("Capped Site", "https://example.com/capped")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        page = json.loads(self.contract.get_page(page_id))
        page["audits_total"] = 12
        page["last_audit_ts"] = 0  # Cooldown expired
        self.contract.pages[page_id] = json.dumps(page)

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.audit_page(page_id)
        self.assertEqual(str(ctx.exception), "maximum audits reached")

    # get_progress diffs
    def test_get_progress_insufficient_audits(self):
        self.contract.register_page("Prog Site", "https://example.com/prog")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        prog = json.loads(self.contract.get_progress(page_id))
        self.assertEqual(prog["status"], "INSUFFICIENT_AUDITS")
        self.assertEqual(prog["full_audits_count"], 0)

    def test_get_progress_deterministic_diffs(self):
        self.contract.register_page("Prog Site", "https://example.com/prog")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        # Audit 1 (bad: score 25, grade F)
        self.contract.audits[f"{page_id}:1"] = json.dumps({
            "n": 1, "mode": "FULL", "score": 25, "grade": "F",
            "rule_counts": {"R1": 3, "R2": 3, "R3": 3, "R4": 4, "R5": 2, "R6": 1, "R7": 1, "R8": 1, "R9": 1, "R10": 2, "R11": 1, "R12": 1}
        })
        # Audit 2 (fixed: score 100, grade A)
        self.contract.audits[f"{page_id}:2"] = json.dumps({
            "n": 2, "mode": "FULL", "score": 100, "grade": "A",
            "rule_counts": {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 0, "R7": 0, "R8": 0, "R9": 0, "R10": 0, "R11": 0, "R12": 0}
        })
        page = json.loads(self.contract.get_page(page_id))
        page["audits_total"] = 2
        self.contract.pages[page_id] = json.dumps(page)

        prog = json.loads(self.contract.get_progress(page_id))
        self.assertEqual(prog["status"], "OK")
        self.assertEqual(prog["score_delta"], 75)
        self.assertEqual(prog["grade_change"]["from"], "F")
        self.assertEqual(prog["grade_change"]["to"], "A")
        self.assertEqual(prog["rule_deltas"]["R1"], -3)
        self.assertEqual(prog["rule_deltas"]["R4"], -4)

    # Pagination bounds
    def test_pagination_bounds(self):
        self.contract.register_page("Page", "https://example.com/p")
        page_id = json.loads(self.contract.list_page_ids(0, 10))[0]

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.list_page_ids(-1, 10)
        self.assertEqual(str(ctx.exception), "invalid pagination")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.list_page_ids(0, 51)
        self.assertEqual(str(ctx.exception), "invalid pagination")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.get_audits(page_id, 0, 0)
        self.assertEqual(str(ctx.exception), "invalid pagination")

        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            self.contract.get_board(0)
        self.assertEqual(str(ctx.exception), "invalid pagination")


if __name__ == "__main__":
    unittest.main()
