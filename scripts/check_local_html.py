#!/usr/bin/env python3
"""Check local HTML links without making external network requests."""

import argparse
import json
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


IGNORED_DIRS = {".git", ".fantastiq-quality", "node_modules", "vendor"}
LINK_ATTRIBUTES = {"href", "src", "action", "poster"}
ACCESSIBILITY_PAGE_LIMIT = 100


class DocumentLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("id", "name"):
            if values.get(key):
                self.anchors.add(values[key])
        for key in LINK_ATTRIBUTES:
            value = values.get(key)
            if value:
                self.links.append((key, value.strip()))

    handle_startendtag = handle_starttag


def html_files(root):
    return sorted(path for path in root.rglob("*.html") if not IGNORED_DIRS.intersection(path.relative_to(root).parts))


def resolve_local_path(root, source, target):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None, parsed.fragment
    raw_path = unquote(parsed.path)
    if raw_path.startswith("/"):
        candidate = root / raw_path.lstrip("/")
    else:
        candidate = source.parent / raw_path
    candidate = Path(posixpath.normpath(str(candidate)))
    try:
        candidate.relative_to(root)
    except ValueError:
        return candidate, parsed.fragment
    if candidate.is_dir():
        candidate = candidate / "index.html"
    elif not candidate.suffix:
        if (candidate / "index.html").is_file():
            candidate = candidate / "index.html"
        elif candidate.with_suffix(".html").is_file():
            candidate = candidate.with_suffix(".html")
    return candidate, parsed.fragment


def check(root):
    pages = html_files(root)
    if not pages:
        return [], ["No HTML pages found under the selected site directory."], []
    parsed_pages = {}
    for page in pages:
        parser = DocumentLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed_pages[page.resolve()] = parser

    failures = []
    checked = []
    for source, parser in parsed_pages.items():
        for attribute, target in parser.links:
            if target.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                if target.startswith("#"):
                    fragment = unquote(target[1:])
                    if fragment and fragment not in parser.anchors:
                        failures.append(f"{source.relative_to(root)}: missing fragment #{fragment}")
                continue
            candidate, fragment = resolve_local_path(root, source, target)
            if candidate is None:
                continue
            checked.append({"source": str(source.relative_to(root)), "attribute": attribute, "target": target})
            try:
                candidate.resolve().relative_to(root.resolve())
            except ValueError:
                failures.append(f"{source.relative_to(root)}: target escapes site root: {target}")
                continue
            if not candidate.is_file():
                failures.append(f"{source.relative_to(root)}: missing local target: {target}")
                continue
            if fragment and candidate.suffix.lower() == ".html":
                target_page = parsed_pages.get(candidate.resolve())
                if target_page is None:
                    target_page = DocumentLinks()
                    try:
                        target_page.feed(candidate.read_text(encoding="utf-8"))
                    except (OSError, UnicodeError) as error:
                        failures.append(f"{source.relative_to(root)}: cannot read {target}: {error}")
                        continue
                if fragment not in target_page.anchors:
                    failures.append(f"{source.relative_to(root)}: missing fragment in {target}: #{fragment}")
    return pages, failures, checked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--pages", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    pages, failures, checked = check(root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    audit_pages = pages[:ACCESSIBILITY_PAGE_LIMIT]
    args.report.write_text(json.dumps({
        "pages": [str(p.relative_to(root)) for p in pages],
        "accessibility_pages": [str(p.relative_to(root)) for p in audit_pages],
        "accessibility_page_limit": ACCESSIBILITY_PAGE_LIMIT,
        "checked_links": checked,
        "failures": failures,
    }, indent=2) + "\n", encoding="utf-8")
    args.pages.write_text("\n".join("/" + p.relative_to(root).as_posix() for p in audit_pages) + "\n", encoding="utf-8")
    print(f"Scanned {len(pages)} HTML files and {len(checked)} local references; axe will scan {len(audit_pages)} pages (limit {ACCESSIBILITY_PAGE_LIMIT}).")
    if len(pages) > ACCESSIBILITY_PAGE_LIMIT:
        print(f"::warning::Only the first {ACCESSIBILITY_PAGE_LIMIT} HTML pages, sorted by path, receive the accessibility scan.")
    if failures:
        for failure in failures:
            print(f"::error::{failure}")
        return 1
    print("No broken local HTML links found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
