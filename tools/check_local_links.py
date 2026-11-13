#!/usr/bin/env python3
"""Check local Markdown links.

This intentionally ignores external URLs and noisy math-like patterns. It is a
small repo maintenance helper, not a full Markdown parser.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
EXTERNAL_RE = re.compile(r"^(https?:|mailto:|tel:|#|javascript:)")


def iter_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not {".git", "node_modules", "_site", "vendor", ".bundle", ".jekyll-cache"}.intersection(path.parts)
    )


def normalize_target(raw: str) -> str | None:
    target = raw.strip()
    if not target or EXTERNAL_RE.match(target):
        return None

    target = target.split("#", 1)[0].strip()
    if not target:
        return None

    # Avoid false positives from old inline math/images that accidentally match.
    if len(target) > 240 or "\n" in target:
        return None
    if len(target) <= 3 and "/" not in target and "." not in target:
        return None

    return unquote(target.replace("\\", "/"))


def main() -> int:
    missing: list[tuple[Path, int, str]] = []

    for path in iter_markdown_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Ignore code fences but retain line numbers for actionable reports.
        text = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*$", lambda m: "\n" * m.group().count("\n"), text)
        for match in LINK_RE.finditer(text):
            target = normalize_target(match.group(1))
            if target is None:
                continue

            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                missing.append((path.relative_to(ROOT), line, match.group(1).strip()))

        class Resources(HTMLParser):
            def handle_starttag(self, tag, attrs):
                for key, raw in attrs:
                    if key not in {"src", "href"} or not raw:
                        continue
                    target = normalize_target(raw)
                    if target is not None and not (path.parent / target).resolve().exists():
                        missing.append((path.relative_to(ROOT), self.getpos()[0], raw))

        Resources().feed(text)

    if missing:
        print(f"Missing local links: {len(missing)}")
        for path, line, target in missing:
            print(f"{path}:{line} -> {target}")
        return 1

    print("All local Markdown/HTML targets exist. Check generated-site anchors with tools/check_site.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
