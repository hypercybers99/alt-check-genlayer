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
from AltCheck import _validate_and_canonicalize_url


class TestUrlPolicy(unittest.TestCase):
    # Valid HTTPS canonicalization tests
    def test_valid_canonical_basic(self):
        url = "https://example.com/path"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/path")

    def test_valid_canonical_uppercase_host(self):
        url = "https://EXAMPLE.COM/about"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/about")

    def test_valid_canonical_query_preserved(self):
        url = "https://example.com/search?q=wcag&sort=desc"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/search?q=wcag&sort=desc")

    def test_valid_canonical_fragment_stripped(self):
        url = "https://example.com/docs#section-2"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/docs")

    def test_valid_canonical_default_port_443(self):
        url = "https://example.com:443/home"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/home")

    def test_valid_canonical_trailing_dot_host(self):
        url = "https://example.com./index.html"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://example.com/index.html")

    def test_valid_punycode_host(self):
        url = "https://xn--e1afmkfd.xn--p1ai/test"
        canonical = _validate_and_canonicalize_url(url)
        self.assertEqual(canonical, "https://xn--e1afmkfd.xn--p1ai/test")

    # Scheme rejections
    def test_reject_http_scheme(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("http://example.com/")
        self.assertEqual(str(ctx.exception), "url must use https")

    def test_reject_ftp_scheme(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("ftp://example.com/file")
        self.assertEqual(str(ctx.exception), "url must use https")

    def test_reject_javascript_scheme(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("javascript:alert(1)")
        self.assertEqual(str(ctx.exception), "url must use https")

    def test_reject_data_scheme(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("data:text/html,<h1>test</h1>")
        self.assertEqual(str(ctx.exception), "url must use https")

    # Credentials
    def test_reject_userinfo_basic(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://user:pass@example.com/")
        self.assertEqual(str(ctx.exception), "url contains credentials")

    def test_reject_userinfo_user_only(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://admin@example.com/")
        self.assertEqual(str(ctx.exception), "url contains credentials")

    # Ports
    def test_reject_explicit_non_443_port_8080(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://example.com:8080/")
        self.assertEqual(str(ctx.exception), "url port not allowed")

    def test_reject_explicit_port_80(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://example.com:80/")
        self.assertEqual(str(ctx.exception), "url port not allowed")

    # Host restrictions
    def test_reject_localhost(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://localhost/api")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_single_label_host(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://internal/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_dot_local(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://service.local/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_dot_internal(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://dashboard.internal/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_dot_onion(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://site.onion/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    # Numeric and IP literal evasion
    def test_reject_ipv4_dotted(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://127.0.0.1/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_ipv4_private_range(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://192.168.1.1/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_ipv4_decimal_integer(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://2130706433/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    def test_reject_ipv6_brackets(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://[::1]/")
        self.assertEqual(str(ctx.exception), "url host not allowed")

    # Length and character hygiene
    def test_reject_overlong_url(self):
        long_url = "https://example.com/" + ("a" * 300)
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url(long_url)
        self.assertEqual(str(ctx.exception), "url too long")

    def test_reject_whitespace_control_chars(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://example.com/bad path")
        self.assertEqual(str(ctx.exception), "url not valid")

    def test_reject_unicode_host_without_punycode(self):
        with self.assertRaises(genlayer.gl.vm.UserError) as ctx:
            _validate_and_canonicalize_url("https://\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444/")
        self.assertEqual(str(ctx.exception), "url not valid")


if __name__ == "__main__":
    unittest.main()
