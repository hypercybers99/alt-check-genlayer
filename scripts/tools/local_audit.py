#!/usr/bin/env python3
"""
Local reference audit implementation for AltCheck.
Directly implements / cross-checks deterministic accessibility rules R1-R12 and SHELL_ONLY detection.
Must match on-chain contract counts exactly on all fixtures.
"""

import sys
import os
import re
import json
import string
import html.parser
import html as html_lib

LABEL_MIN = 3
LABEL_MAX = 80
AUDIT_COOLDOWN_SECONDS = 300
MAX_AUDITS_PER_PAGE = 12
NOTE_MIN = 5
NOTE_MAX = 280
MAX_NOTES_PER_AUDIT = 3
SNIPPET_MAX = 120
MAX_SNIPPETS_PER_RULE = 5
SHELL_TEXT_THRESHOLD = 200
MODEL_ALT_SAMPLE = 8
MODEL_LINK_SAMPLE = 8
MODEL_PENALTY_PER_VAGUE = 2
MODEL_PENALTY_CAP = 10
PAGE_LIMIT_MAX = 50
MAX_BODY_BYTES = 300000
MAX_ELEMENTS = 3000

RULE_IDS = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12"]

RULE_SPECS = {
    "R1": {"id": "R1", "wcag": "1.1.1", "weight": 4, "cap": 8, "desc": "Images without alt attribute"},
    "R2": {"id": "R2", "wcag": "1.1.1", "weight": 2, "cap": 8, "desc": "Poor or filename-like alt text"},
    "R3": {"id": "R3", "wcag": "1.3.1, 3.3.2, 4.1.2", "weight": 4, "cap": 8, "desc": "Form controls without an accessible name"},
    "R4": {"id": "R4", "wcag": "2.4.4, 4.1.2", "weight": 3, "cap": 8, "desc": "Links/buttons without an accessible name or with generic text"},
    "R5": {"id": "R5", "wcag": "1.3.1, 2.4.6", "weight": 3, "cap": 3, "desc": "Heading structure errors (missing h1, multiple h1, skipped levels)"},
    "R6": {"id": "R6", "wcag": "3.1.1", "weight": 5, "cap": 1, "desc": "html lang attribute missing or empty"},
    "R7": {"id": "R7", "wcag": "2.4.2", "weight": 5, "cap": 1, "desc": "title element missing or empty"},
    "R8": {"id": "R8", "wcag": "4.1.1", "weight": 2, "cap": 5, "desc": "Duplicate id attributes"},
    "R9": {"id": "R9", "wcag": "1.4.4", "weight": 5, "cap": 1, "desc": "Viewport meta disabling user zoom"},
    "R10": {"id": "R10", "wcag": "2.4.3", "weight": 2, "cap": 5, "desc": "Positive tabindex attributes"},
    "R11": {"id": "R11", "wcag": "1.3.1, 2.4.1", "weight": 3, "cap": 1, "desc": "No main landmark and no role=main"},
    "R12": {"id": "R12", "wcag": "4.1.2", "weight": 3, "cap": 5, "desc": "iframe without title or aria-label"},
}

GENERIC_ALT_WORDS = {
    "image", "picture", "photo", "graphic", "icon", "thumbnail",
    "bild", "grafik", "foto",
    "imagen", "grafico",
    "hinh anh", "anh", "hinh",
    "graphique",
}

IMAGE_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"
)

GENERIC_LINK_PHRASES = {
    "click here", "read more", "here", "more", "link", "learn more", "this", "details",
    "continue", "go", "button", "view", "info",
    "haz clic aqui", "haga clic aqui", "leer mas", "mas", "enlace", "detalles",
    "bam vao day", "nhap vao day", "xem them", "them", "chi tiet", "tai day", "lien ket",
    "cliquez ici", "en savoir plus", "lire la suite", "plus", "lien",
    "hier klicken", "mehr lesen", "weiter",
}

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}


def is_punctuation_or_space_only(s: str) -> bool:
    if not s:
        return True
    return not any(c.isalnum() for c in s)


class ElementNode:
    def __init__(self, tag: str, attrs: dict, raw_tag: str, parent=None):
        self.tag = tag.lower()
        self.attrs = {k.lower(): v for k, v in attrs.items() if k is not None}
        self.raw_tag = raw_tag
        self.parent = parent
        self.children = []
        self.text_parts = []
        self.child_imgs = []

    def get_text(self) -> str:
        res = " ".join("".join(self.text_parts).split())
        return res


class DOMParser(html.parser.HTMLParser):
    def __init__(self, raw_html: str):
        super().__init__()
        self.raw_html = raw_html
        self.elements = []
        self.root_elements = []
        self.stack = []
        self.id_map = {}
        self.labels_by_for = {}
        self.html_lang = ""
        self.has_html_tag = False
        self.title_text = ""
        self.viewport_content = None
        self.has_main = False
        self.headings = []
        self.h1_count = 0
        self.script_tag_count = 0
        self.visible_text_parts = []
        self.ignored_stack = 0
        self.title_stack = 0
        self.elements_seen = 0
        self.elements_dropped = 0

    def handle_starttag(self, tag, attrs):
        self.elements_seen += 1
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v if v is not None else "") for k, v in attrs if k is not None}
        raw_snippet = self.get_starttag_text() or f"<{tag}>"

        if tag_lower == "html":
            self.has_html_tag = True
            self.html_lang = attr_dict.get("lang", "").lower()

        if tag_lower == "meta" and attr_dict.get("name", "").lower() == "viewport":
            self.viewport_content = attr_dict.get("content", "")

        if tag_lower == "script":
            self.script_tag_count += 1

        if tag_lower in ("script", "style", "noscript", "template"):
            self.ignored_stack += 1

        if tag_lower == "title":
            self.title_stack += 1

        parent = self.stack[-1] if self.stack else None
        node = ElementNode(tag_lower, attr_dict, raw_snippet, parent)

        if len(self.elements) < MAX_ELEMENTS:
            self.elements.append(node)
        else:
            self.elements_dropped += 1

        if parent is not None:
            parent.children.append(node)
            if tag_lower == "img":
                p = parent
                while p:
                    p.child_imgs.append(node)
                    p = p.parent
        else:
            self.root_elements.append(node)

        elem_id = attr_dict.get("id")
        if elem_id:
            if elem_id not in self.id_map:
                self.id_map[elem_id] = []
            self.id_map[elem_id].append(node)

        if tag_lower == "label" and "for" in attr_dict:
            for_id = attr_dict["for"]
            if for_id not in self.labels_by_for:
                self.labels_by_for[for_id] = []
            self.labels_by_for[for_id].append(node)

        if tag_lower == "main" or attr_dict.get("role", "").lower() == "main":
            self.has_main = True

        if re.match(r"^h[1-6]$", tag_lower):
            level = int(tag_lower[1])
            if level == 1:
                self.h1_count += 1
            self.headings.append((level, node))

        if tag_lower not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "template") and self.ignored_stack > 0:
            self.ignored_stack -= 1
        if tag_lower == "title" and self.title_stack > 0:
            self.title_stack -= 1

        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag_lower:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if not data:
            return
        if self.title_stack > 0:
            self.title_text += data

        if self.stack and self.ignored_stack == 0:
            self.stack[-1].text_parts.append(data)
            p = self.stack[-1].parent
            while p:
                p.text_parts.append(data)
                p = p.parent

        if self.ignored_stack == 0:
            clean_str = data.strip()
            if clean_str:
                self.visible_text_parts.append(clean_str)


def compute_accessible_name(el: ElementNode, parser: DOMParser) -> str:
    # 1. aria-labelledby
    if "aria-labelledby" in el.attrs:
        ids = el.attrs["aria-labelledby"].split()
        resolved_texts = []
        for id_val in ids:
            targets = parser.id_map.get(id_val, [])
            for t in targets:
                txt = t.get_text()
                if txt:
                    resolved_texts.append(txt)
        combined = " ".join(" ".join(resolved_texts).split())
        if combined and not is_punctuation_or_space_only(combined):
            return combined

    # 2. aria-label
    if "aria-label" in el.attrs:
        al = " ".join(el.attrs["aria-label"].split())
        if al and not is_punctuation_or_space_only(al):
            return al

    # 3. label[for=id]
    el_id = el.attrs.get("id")
    if el_id and el_id in parser.labels_by_for:
        lbl_texts = []
        for lbl in parser.labels_by_for[el_id]:
            lt = lbl.get_text()
            if lt:
                lbl_texts.append(lt)
        combined = " ".join(" ".join(lbl_texts).split())
        if combined and not is_punctuation_or_space_only(combined):
            return combined

    # 4. wrapping <label>
    p = el.parent
    while p:
        if p.tag == "label":
            lt = p.get_text()
            if lt and not is_punctuation_or_space_only(lt):
                return lt
        p = p.parent

    # 5. title
    if "title" in el.attrs:
        t = " ".join(el.attrs["title"].split())
        if t and not is_punctuation_or_space_only(t):
            return t

    # 6. visible text content (for links / buttons, including img alt of child images)
    if el.tag in ("a", "button"):
        direct_text = el.get_text()
        img_alts = []
        for img in el.child_imgs:
            alt = img.attrs.get("alt", "").strip()
            if alt:
                img_alts.append(alt)
        parts = []
        if direct_text:
            parts.append(direct_text)
        if img_alts:
            parts.extend(img_alts)
        combined = " ".join(" ".join(parts).split())
        if combined and not is_punctuation_or_space_only(combined):
            return combined

    # 7. value for input submit / button / reset
    if el.tag == "input" and el.attrs.get("type", "").lower() in ("submit", "button", "reset"):
        val = " ".join(el.attrs.get("value", "").split())
        if val and not is_punctuation_or_space_only(val):
            return val

    return ""


def run_audit_on_html(raw_html: str, model_penalty: int = 0) -> dict:
    truncated = False
    if len(raw_html.encode("utf-8")) > MAX_BODY_BYTES:
        raw_html = raw_html.encode("utf-8")[:MAX_BODY_BYTES].decode("utf-8", errors="replace")
        truncated = True

    parser = DOMParser(raw_html)
    try:
        parser.feed(raw_html)
    except Exception:
        pass

    visible_text = " ".join(parser.visible_text_parts)
    visible_text_len = len(visible_text)

    # Check SHELL_ONLY condition
    is_shell_container = False
    for r in parser.root_elements:
        if r.attrs.get("id") in ("root", "app", "__next", "__nuxt"):
            is_shell_container = True
            break
    if not is_shell_container:
        for el in parser.elements:
            if el.attrs.get("id") in ("root", "app", "__next", "__nuxt"):
                if len(el.get_text()) < 50:
                    is_shell_container = True
                    break

    mode = "FULL"
    if visible_text_len < SHELL_TEXT_THRESHOLD and (parser.script_tag_count > 0 or is_shell_container):
        mode = "SHELL_ONLY"

    rule_counts = {f"R{i}": 0 for i in range(1, 13)}
    snippets = {f"R{i}": [] for i in range(1, 13)}
    decorative_unmarked = 0

    def add_snippet(rule_id: str, snippet: str):
        if not snippet:
            return
        snip_clean = snippet.strip()[:SNIPPET_MAX]
        if snip_clean in raw_html:
            if len(snippets[rule_id]) < MAX_SNIPPETS_PER_RULE:
                snippets[rule_id].append(snip_clean)

    # Head-level rules evaluated in both FULL and SHELL_ONLY modes
    # R6: <html lang>
    if not parser.has_html_tag or not parser.html_lang.strip():
        rule_counts["R6"] = 1
        add_snippet("R6", "<html>")

    # R7: <title>
    if not parser.title_text.strip():
        rule_counts["R7"] = 1
        add_snippet("R7", "<title></title>")

    # R9: Viewport meta zoom
    if parser.viewport_content is not None:
        vc = parser.viewport_content.lower().replace(" ", "")
        zoom_disabled = False
        if "user-scalable=no" in vc or "user-scalable=0" in vc:
            zoom_disabled = True
        match_max = re.search(r"maximum-scale=([0-9.]+)", vc)
        if match_max:
            try:
                scale_val = float(match_max.group(1))
                if scale_val < 2.0:
                    zoom_disabled = True
            except ValueError:
                pass
        if zoom_disabled:
            rule_counts["R9"] = 1
            add_snippet("R9", f'<meta name="viewport" content="{parser.viewport_content}">')

    if mode == "FULL":
        # R1 & R2: Images
        for el in parser.elements:
            if el.tag == "img":
                if "alt" not in el.attrs:
                    rule_counts["R1"] += 1
                    add_snippet("R1", el.raw_tag)
                else:
                    alt_val = el.attrs["alt"].strip()
                    if alt_val == "":
                        role_val = el.attrs.get("role", "").lower()
                        aria_hidden = el.attrs.get("aria-hidden", "").lower()
                        if role_val in ("presentation", "none") or aria_hidden == "true":
                            pass  # valid decorative
                        else:
                            decorative_unmarked += 1
                    else:
                        # Check R2 poor alt
                        is_poor = False
                        alt_lower = alt_val.lower()
                        if any(alt_lower.endswith(ext) for ext in IMAGE_EXTENSIONS):
                            is_poor = True
                        elif re.match(r"^(?:img|dsc|image|screenshot|untitled|photo)[\W_\d]*$", alt_lower):
                            is_poor = True
                        elif alt_lower in GENERIC_ALT_WORDS:
                            is_poor = True
                        if is_poor:
                            rule_counts["R2"] += 1
                            add_snippet("R2", el.raw_tag)

        # R3: Form controls without accessible name
        for el in parser.elements:
            if el.tag in ("input", "select", "textarea"):
                if el.tag == "input" and el.attrs.get("type", "").lower() in ("hidden", "submit", "button", "image", "reset"):
                    continue
                acc_name = compute_accessible_name(el, parser)
                if not acc_name:
                    rule_counts["R3"] += 1
                    add_snippet("R3", el.raw_tag)

        # R4: Links / buttons without accessible name or generic phrase
        for el in parser.elements:
            if el.tag == "button" or (el.tag == "a" and "href" in el.attrs):
                acc_name = compute_accessible_name(el, parser)
                if not acc_name:
                    rule_counts["R4"] += 1
                    add_snippet("R4", el.raw_tag)
                else:
                    norm_name = re.sub(r"[^\w\s]", "", acc_name.lower()).strip()
                    if norm_name in GENERIC_LINK_PHRASES:
                        rule_counts["R4"] += 1
                        add_snippet("R4", el.raw_tag)

        # R5: Heading structure
        r5_findings = 0
        if parser.h1_count == 0:
            r5_findings += 1
            add_snippet("R5", "<!-- missing h1 -->")
        elif parser.h1_count > 1:
            r5_findings += 1
            if len(parser.headings) > 1:
                for lvl, hnode in parser.headings:
                    if lvl == 1:
                        add_snippet("R5", hnode.raw_tag)
                        break

        prev_level = None
        for lvl, hnode in parser.headings:
            if prev_level is not None:
                if lvl > prev_level + 1:
                    r5_findings += 1
                    add_snippet("R5", hnode.raw_tag)
            prev_level = lvl
        rule_counts["R5"] = min(RULE_SPECS["R5"]["cap"], r5_findings)

        # R8: Duplicate IDs
        dup_count = 0
        for eid, elist in parser.id_map.items():
            if len(elist) > 1:
                dup_count += 1
                add_snippet("R8", elist[0].raw_tag)
        rule_counts["R8"] = dup_count

        # R10: Positive tabindex
        for el in parser.elements:
            if "tabindex" in el.attrs:
                try:
                    ti = int(el.attrs["tabindex"])
                    if ti > 0:
                        rule_counts["R10"] += 1
                        add_snippet("R10", el.raw_tag)
                except ValueError:
                    pass

        # R11: Main landmark
        if not parser.has_main:
            rule_counts["R11"] = 1
            add_snippet("R11", "<body>")

        # R12: iframe title
        for el in parser.elements:
            if el.tag == "iframe":
                has_title = bool(el.attrs.get("title", "").strip())
                has_label = bool(el.attrs.get("aria-label", "").strip() or el.attrs.get("aria-labelledby", "").strip())
                if not has_title and not has_label:
                    rule_counts["R12"] += 1
                    add_snippet("R12", el.raw_tag)

    # Element metrics & partial audit tracking
    elements_seen = parser.elements_seen
    elements_analyzed = len(parser.elements)
    elements_truncated = parser.elements_dropped > 0
    is_partial = truncated or elements_truncated

    unverified_rules = []
    if is_partial and mode == "FULL":
        for r_id in ("R5", "R8", "R11"):
            if rule_counts[r_id] == 0:
                unverified_rules.append(r_id)

    # Compute score and grade
    partial_note = ""
    if mode == "SHELL_ONLY":
        score = -1
        grade = "N/A"
    else:
        deductions = 0
        for r_id, spec in RULE_SPECS.items():
            cnt = rule_counts[r_id]
            deductions += spec["weight"] * min(cnt, spec["cap"])
        det_score = max(0, 100 - deductions)
        score = max(0, det_score - model_penalty)
        if is_partial:
            if score >= 80:
                grade = "B"
            elif score >= 65:
                grade = "C"
            elif score >= 50:
                grade = "D"
            else:
                grade = "F"
            partial_note = f"partial audit: only the first {len(raw_html.encode('utf-8'))} bytes / {elements_analyzed} elements were analyzed"
        else:
            if score >= 90:
                grade = "A"
            elif score >= 80:
                grade = "B"
            elif score >= 65:
                grade = "C"
            elif score >= 50:
                grade = "D"
            else:
                grade = "F"

    return {
        "mode": mode,
        "score": score,
        "grade": grade,
        "rule_counts": rule_counts,
        "snippets": snippets,
        "decorative_unmarked": decorative_unmarked,
        "visible_text_chars": visible_text_len,
        "script_tag_count": parser.script_tag_count,
        "truncated": truncated,
        "elements_seen": elements_seen,
        "elements_analyzed": elements_analyzed,
        "elements_truncated": elements_truncated,
        "partial": is_partial,
        "partial_note": partial_note,
        "unverified_rules": unverified_rules,
    }


def main():
    fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fixtures-local")
    if len(sys.argv) > 1:
        target = sys.argv[1]
        with open(target, "r", encoding="utf-8") as f:
            res = run_audit_on_html(f.read())
            print(json.dumps(res, indent=2))
        return

    print("Running local audit reference across all fixtures in fixtures-local/...\n")
    for fname in sorted(os.listdir(fixtures_dir)):
        if fname.endswith(".html"):
            fpath = os.path.join(fixtures_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                res = run_audit_on_html(f.read())
            print(f"=== {fname} ===")
            print(f"Mode: {res['mode']} | Score: {res['score']} | Grade: {res['grade']}")
            print("Rule counts:", {k: v for k, v in res['rule_counts'].items() if v > 0})
            if res["decorative_unmarked"]:
                print("Decorative unmarked:", res["decorative_unmarked"])
            print()

if __name__ == "__main__":
    main()
