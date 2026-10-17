# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import hashlib
from genlayer import *


class Probe(gl.Contract):
    last_probe_result: str

    def __init__(self):
        self.last_probe_result = "{}"

    @gl.public.view
    def get_result(self) -> str:
        return self.last_probe_result

    @gl.public.write
    def probe_p1_p2_capabilities(self, url: str) -> None:
        def leader() -> str:
            res = {}
            # P1: Inspect web.get
            try:
                resp = gl.nondet.web.get(url)
                resp_attrs = [a for a in dir(resp) if not a.startswith("_")]
                headers_info = {}
                if hasattr(resp, "headers") and resp.headers is not None:
                    try:
                        for k, v in resp.headers.items():
                            val_str = v.decode("utf-8", errors="replace") if isinstance(v, (bytes, bytearray)) else str(v)
                            headers_info[str(k)] = val_str
                    except Exception as he:
                        headers_info["_err"] = str(he)
                body_val = resp.body if hasattr(resp, "body") else None
                body_len = len(body_val) if body_val is not None else 0
                body_sample = ""
                if body_val is not None:
                    if isinstance(body_val, (bytes, bytearray)):
                        body_sample = body_val[:200].decode("utf-8", errors="replace")
                    else:
                        body_sample = str(body_val)[:200]

                res["web_get"] = {
                    "status": int(resp.status) if hasattr(resp, "status") else None,
                    "attrs": resp_attrs,
                    "headers_keys": list(headers_info.keys()),
                    "content_type": headers_info.get("content-type") or headers_info.get("Content-Type") or "",
                    "body_len": body_len,
                    "body_sample": body_sample,
                    "has_url": hasattr(resp, "url"),
                    "url_val": str(getattr(resp, "url", "")),
                }
            except Exception as e:
                res["web_get_err"] = str(e)

            # P2: Test html.parser and html.unescape
            try:
                import html.parser
                class TestParser(html.parser.HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.tags = []
                    def handle_starttag(self, tag, attrs):
                        self.tags.append((tag, dict(attrs)))
                p = TestParser()
                p.feed("<div class=\"demo\"><img src=\"test.png\" alt=\"photo\"><h1>Title</h1></div>")
                res["html_parser"] = {
                    "importable": True,
                    "tags": p.tags,
                }
            except Exception as e:
                res["html_parser"] = {
                    "importable": False,
                    "err": str(e),
                }

            try:
                import html
                unesc = html.unescape("&lt;tag attr=&quot;val&quot;&gt; &amp; copy&#169;")
                res["html_unescape"] = {
                    "importable": True,
                    "sample": unesc,
                }
            except Exception as e:
                res["html_unescape"] = {
                    "importable": False,
                    "err": str(e),
                }

            return json.dumps(res)

        def validator(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            data = str(leaders_res.calldata)
            try:
                parsed = json.loads(data)
                return "web_get" in parsed or "web_get_err" in parsed
            except Exception:
                return False

        res = gl.vm.run_nondet_unsafe(leader, validator)
        self.last_probe_result = str(res)

    @gl.public.write
    def probe_fetch_size_and_consistency(self, url: str) -> None:
        def leader() -> str:
            res = {}
            try:
                resp = gl.nondet.web.get(url)
                b = resp.body
                body_bytes = b if isinstance(b, (bytes, bytearray)) else (b.encode("utf-8") if b else b"")
                sha256 = hashlib.sha256(body_bytes).hexdigest()
                text = body_bytes.decode("utf-8", errors="replace")
                res = {
                    "url": url,
                    "status": int(resp.status) if hasattr(resp, "status") else -1,
                    "body_len": len(body_bytes),
                    "body_sha256": sha256,
                    "img_count": text.count("<img"),
                    "a_count": text.count("<a"),
                    "h1_count": text.count("<h1"),
                }
            except Exception as e:
                res = {"url": url, "error": str(e)}
            return json.dumps(res)

        def validator(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            data = str(leaders_res.calldata)
            try:
                ld = json.loads(data)
                if "error" in ld:
                    return False
            except Exception:
                return False

            def val_fetch() -> str:
                try:
                    resp = gl.nondet.web.get(url)
                    b = resp.body
                    body_bytes = b if isinstance(b, (bytes, bytearray)) else (b.encode("utf-8") if b else b"")
                    sha256 = hashlib.sha256(body_bytes).hexdigest()
                    text = body_bytes.decode("utf-8", errors="replace")
                    return json.dumps({
                        "body_len": len(body_bytes),
                        "body_sha256": sha256,
                        "img_count": text.count("<img"),
                        "a_count": text.count("<a"),
                        "h1_count": text.count("<h1"),
                    })
                except Exception as e:
                    return json.dumps({"error": str(e)})

            sand_res = gl.vm.spawn_sandbox(val_fetch)
            if not isinstance(sand_res, gl.vm.Return):
                return False
            try:
                vd = json.loads(str(sand_res.calldata))
                if "error" in vd:
                    return False
                # compare sha256 and counts
                return (
                    vd.get("img_count") == ld.get("img_count") and
                    vd.get("a_count") == ld.get("a_count") and
                    vd.get("h1_count") == ld.get("h1_count")
                )
            except Exception:
                return False

        res = gl.vm.run_nondet_unsafe(leader, validator)
        self.last_probe_result = str(res)

    @gl.public.write
    def probe_prompt_batch(self, prompt_text: str) -> None:
        def leader() -> str:
            raw = gl.nondet.exec_prompt(
                prompt_text,
                response_format="json"
            )
            return json.dumps({"raw": raw})

        def validator(leaders_res: gl.vm.Result) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            data = str(leaders_res.calldata)
            try:
                d = json.loads(data)
                return "raw" in d and len(str(d["raw"])) > 0
            except Exception:
                return False

        res = gl.vm.run_nondet_unsafe(leader, validator)
        self.last_probe_result = str(res)
