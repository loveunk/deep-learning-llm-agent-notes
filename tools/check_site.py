#!/usr/bin/env python3
"""Validate local paths, resources and anchors against actual Jekyll output.

No network requests. This checks published HTML, not external availability or
whether model examples are executable. Run after the same build used to deploy.
"""

from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[int, str]] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("id", "name" if tag == "a" else "id"):
            if attrs.get(key):
                self.ids.add(attrs[key])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append((self.getpos()[0], attrs[key]))


def resolve_target(site: Path, source: Path, url: str, baseurl: str):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if path.startswith("/"):
        if baseurl and path != baseurl and not path.startswith(baseurl + "/"):
            raise ValueError(f"absolute path escapes baseurl: {path}")
        path = path[len(baseurl):].lstrip("/")
        target = site / path
    elif path:
        target = source.parent / path
    else:
        target = source
    target = target.resolve()
    if target != site and site not in target.parents:
        raise ValueError("path escapes site directory")
    if target.is_dir():
        target = target / "index.html"
    return target, unquote(parsed.fragment)


def check_site(site: Path, baseurl: str) -> tuple[list[str], int]:
    site = site.resolve()
    pages = {path: Page(path.read_text(encoding="utf-8")) for path in site.rglob("*.html")}
    errors: list[str] = []
    checked = 0
    if not (site / "index.html").is_file():
        return ["missing index.html; build the site first"], 0
    for path, page in pages.items():
        for line, url in page.links:
            try:
                resolved = resolve_target(site, path, url, baseurl)
                if resolved is None:
                    continue
                checked += 1
                target, anchor = resolved
                if not target.is_file():
                    raise ValueError("missing local target")
                if anchor and target.suffix == ".html":
                    # Text fragments are a browser feature, not element ids.
                    anchor = anchor.split(":~:text=", 1)[0]
                    if anchor and anchor not in pages[target].ids:
                        raise ValueError(f"missing anchor #{anchor}")
            except (ValueError, KeyError) as exc:
                errors.append(f"{path.relative_to(site)}:{line}: {url} ({exc})")
    index = site / "search.json"
    if index.is_file():
        try:
            entries = json.loads(index.read_text(encoding="utf-8"))
            if not isinstance(entries, list) or not entries:
                raise ValueError("search index must be a nonempty array")
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get("title") or not entry.get("url"):
                    raise ValueError("search entry is missing title or url")
                resolved = resolve_target(site, site / "index.html", entry["url"], baseurl)
                if resolved is None or not resolved[0].is_file():
                    raise ValueError(f"search target is missing: {entry['url']}")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"search.json: {exc}")
    else:
        errors.append("missing search.json; the site search cannot work")
    return errors, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("_site"))
    parser.add_argument("--baseurl", default="")
    args = parser.parse_args()
    errors, checked = check_site(args.site, args.baseurl.rstrip("/"))
    for error in errors:
        print(error)
    print(f"Checked {checked} local HTML links/resources; {len(errors)} errors.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
