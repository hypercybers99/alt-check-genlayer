import unittest
import sys
import os

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

root_dir = os.path.dirname(pkg_dir)
contracts_dir = os.path.join(root_dir, "contracts")
tools_dir = os.path.join(root_dir, "scripts", "tools")
fixtures_dir = os.path.join(root_dir, "fixtures-local")

if contracts_dir not in sys.path:
    sys.path.insert(0, contracts_dir)
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from AltCheck import _evaluate_deterministic_rules
import local_audit
import scan_ascii
import scan_banned_words


class TestParityAndScans(unittest.TestCase):
    def test_local_audit_parity_across_all_fixtures(self):
        fixture_files = [f for f in sorted(os.listdir(fixtures_dir)) if f.endswith(".html")]
        self.assertGreaterEqual(len(fixture_files), 5)

        for fname in fixture_files:
            fpath = os.path.join(fixtures_dir, fname)
            with open(fpath, "r", encoding="utf-8") as fp:
                content = fp.read()

            ref_res = local_audit.run_audit_on_html(content)
            contract_res = _evaluate_deterministic_rules(content)

            self.assertEqual(
                ref_res["mode"],
                contract_res["mode"],
                f"Mode mismatch for fixture {fname}: ref {ref_res['mode']} vs contract {contract_res['mode']}"
            )

            for r_id in local_audit.RULE_IDS:
                ref_count = ref_res["rule_counts"].get(r_id, 0)
                contract_count = contract_res["rule_counts"].get(r_id, 0)
                self.assertEqual(
                    ref_count,
                    contract_count,
                    f"Count mismatch on {fname} for rule {r_id}: local_audit {ref_count} vs contract {contract_count}"
                )

    def test_ascii_scan_passes(self):
        for fname in os.listdir(contracts_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(contracts_dir, fname)
                non_ascii = scan_ascii.check_ascii(fpath)
                self.assertEqual(
                    len(non_ascii), 0,
                    f"Non-ASCII characters detected in {fname}: {non_ascii[:5]}"
                )

    def test_banned_words_scan_passes(self):
        # We invoke the scan logic from scan_banned_words
        violations = []
        for r, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in scan_banned_words.IGNORE_DIRS]
            for f in files:
                if f in scan_banned_words.ALLOWED_FILES:
                    continue
                if not f.endswith(('.ts', '.tsx', '.js', '.jsx', '.json', '.md', '.html', '.py', '.css', '.mjs')):
                    continue
                path = os.path.join(r, f)
                rel_path = os.path.relpath(path, root_dir).replace('\\', '/')
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    for line_idx, line in enumerate(fp, 1):
                        for pat, name in scan_banned_words.BANNED_PATTERNS:
                            m = scan_banned_words.re.search(pat, line, scan_banned_words.re.IGNORECASE)
                            if m:
                                violations.append((rel_path, line_idx, m.group(0), line.strip()))
        self.assertEqual(
            len(violations), 0,
            f"Banned words detected: {violations}"
        )


if __name__ == "__main__":
    unittest.main()
