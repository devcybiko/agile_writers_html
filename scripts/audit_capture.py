#!/usr/bin/env python3
"""Audit a wget capture or static site without changing its contents."""

import argparse
from collections import Counter, defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


SITE_HOSTS = {"agilewriters.com", "www.agilewriters.com"}
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)|@import\s+['\"]([^'\"]+)", re.I)
WP_ENDPOINT = re.compile(r"(?:/wp-json(?:/|\?|$)|/wp-admin(?:/|\?|$)|/wp-login\.php|/xmlrpc\.php|/wp-comments-post\.php)", re.I)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.features = []
        self.inline_css = []
        self.in_style = False
        self.classified = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        marker = " ".join((attrs.get("id", ""), attrs.get("class", ""), attrs.get("name", "")))
        if re.search(r"(?:^|[\s_-])(search|comment|respond)(?:$|[\s_-])", marker, re.I):
            self.features.append(("possible search/comment markup", f"{tag}: {marker.strip()}"))
        for name in ("href", "src", "action", "poster", "data-src"):
            if attrs.get(name):
                self.references.append((tag + "[" + name + "]", attrs[name]))
                if tag == "a" and name == "href":
                    category = "navigation"
                elif tag == "link":
                    category = "resource" if "stylesheet" in attrs.get("rel", "").lower().split() else "metadata"
                elif name == "action":
                    category = "form_action"
                else:
                    category = "resource"
                self.classified.append((category, attrs[name]))
        for name in ("srcset", "data-srcset"):
            for part in attrs.get(name, "").split(","):
                if part.strip():
                    self.references.append((tag + "[" + name + "]", part.strip().split()[0]))
        if attrs.get("style"):
            self.inline_css.append(attrs["style"])
        if tag == "style":
            self.in_style = True
        if tag in ("form", "iframe", "base"):
            self.features.append((tag, attrs.get("action") or attrs.get("src") or attrs.get("href") or "(none)"))
        if tag == "input" and (attrs.get("type", "").lower() == "search" or attrs.get("name", "").lower() == "s"):
            self.features.append(("search input", attrs.get("name", "(unnamed)")))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.inline_css.append(data)


def css_references(text):
    return [("css", (m.group(1) or m.group(2)).strip()) for m in CSS_URL.finditer(text)]


def classify_file(path):
    name = path.name.lower().split("?", 1)[0]
    # Wget appends an extension after the query for some HTML and CSS files.
    if path.name.lower().endswith(".html") or name.endswith((".html", ".htm")):
        with path.open('rb') as stream:
            prefix = stream.read(512).lstrip().lower()
        if prefix.startswith(b'<?xml') and (b'<rss' in prefix or b'<feed' in prefix):
            return "feed"
        return "html"
    if path.name.lower().endswith(".css") or name.endswith(".css"):
        return "css"
    if name.endswith((".js", ".mjs")):
        return "javascript"
    if name.endswith((".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".avif")):
        return "images"
    if name.endswith((".woff", ".woff2", ".ttf", ".otf", ".eot")):
        return "fonts"
    return "other"


def local_candidates(root, source, reference):
    """Return in-root candidates, including wget's literal-query filenames."""
    parsed = urlsplit(reference)
    path = unquote(parsed.path)
    base = root if path.startswith("/") else source.parent
    relative = path.lstrip("/") if path.startswith("/") else path
    raw = base / relative
    candidates = []
    if parsed.query:
        # Encoded query characters can be literal characters in wget filenames.
        for query in (parsed.query, unquote(parsed.query)):
            candidates.extend([Path(str(raw) + "?" + query), Path(str(raw) + "?" + query + ".html"), Path(str(raw) + "?" + query + ".css")])
    candidates.extend([raw, raw / "index.html", Path(str(raw) + ".html")])
    return [p for p in candidates if p.resolve().is_relative_to(root.resolve())]


def audit(root):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    # A capture has a host directory; a built site normally has index.html at root.
    if not (root / "index.html").is_file() and (root / "agilewriters.com").is_dir():
        root = root / "agilewriters.com"
    files = sorted(p for p in root.rglob("*") if p.is_file())
    counts = Counter(classify_file(p) for p in files)
    missing = defaultdict(list)
    external = Counter()
    external_resources = Counter()
    production = Counter()
    production_missing = defaultdict(list)
    endpoints = Counter()
    features = defaultdict(list)
    uncertain = defaultdict(list)
    parse_errors = []
    classified = defaultdict(list)
    references = 0

    def record(bucket, key, source):
        bucket[key].append(source)

    for file in files:
        kind = classify_file(file)
        if kind not in ("html", "css"):
            continue
        source = str(file.relative_to(root))
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
            if kind == "html":
                parser = PageParser()
                parser.feed(text)
                refs = parser.references + [r for css in parser.inline_css for r in css_references(css)]
                for category, ref in parser.classified:
                    parsed_ref = urlsplit(ref)
                    if parsed_ref.netloc:
                        record(classified, f"{category}: {ref}", source)
                for feature, detail in parser.features:
                    record(features, feature + ": " + detail, source)
            else:
                refs = css_references(text)
        except (OSError, ValueError) as exc:
            parse_errors.append({"file": source, "error": str(exc)})
            continue
        for context, ref in refs:
            ref = ref.strip()
            if not ref or ref.startswith("#"):
                continue
            references += 1
            parsed = urlsplit(ref)
            if parsed.scheme.lower() in ("data", "mailto", "tel", "javascript", "blob"):
                continue
            if WP_ENDPOINT.search(ref):
                endpoints[ref] += 1
            if parsed.netloc:
                host = (parsed.hostname or "").lower()
                if host in SITE_HOSTS:
                    production[ref] += 1
                    local_ref = parsed.path or "/"
                    if parsed.query:
                        local_ref += "?" + parsed.query
                    if not any(p.is_file() for p in local_candidates(root, file, local_ref)):
                        record(production_missing, f"{context}: {ref}", source)
                else:
                    external[host or parsed.netloc] += 1
                    if context.startswith(("img[", "script[", "link[", "iframe[", "source[", "video[", "css")):
                        external_resources[host or parsed.netloc] += 1
                continue
            if parsed.scheme:
                record(uncertain, f"{context}: {ref}", source)
                continue
            candidates = local_candidates(root, file, ref)
            if not any(p.is_file() for p in candidates):
                # A query can be a dynamic request, not a file wget should have captured.
                bucket = uncertain if parsed.query else missing
                record(bucket, f"{context}: {ref}", source)

    def summarize(bucket):
        return [{"reference": key, "occurrences": len(values), "sources": sorted(set(values))[:10]} for key, values in sorted(bucket.items(), key=lambda x: (-len(x[1]), x[0]))]

    return {
        "root": str(root), "files_total": len(files), "file_types": dict(sorted(counts.items())),
        "references_examined": references, "missing_local": summarize(missing),
        "uncertain_references": summarize(uncertain), "external_hosts": dict(external.most_common()),
        "external_resource_hosts": dict(external_resources.most_common()),
        "production_without_local_candidate": summarize(production_missing),
        "production_urls": dict(production.most_common()), "wordpress_endpoints": dict(endpoints.most_common()),
        "features": summarize(features), "parse_errors": parse_errors,
        "classified_external_references": summarize(classified),
        "limitations": "Static HTML/CSS inspection only; RSS feed snapshots are counted separately and their contents are not parsed. JavaScript-generated requests, dynamic behavior, unusual srcset syntax, and CSS parsing edge cases need browser review. Local candidates for absolute URLs are heuristic, not proof of equivalence. External resource hosts may include metadata links. A missing reference may be unused or intentionally dynamic.",
    }


def markdown(result):
    lines = ["# Capture audit", "", f"Root: `{result['root']}`", f"Files: **{result['files_total']}**", f"References examined: **{result['references_examined']}**", "", "## File types"]
    lines.extend(f"- {key}: {value}" for key, value in result["file_types"].items())
    for key, title in (("missing_local", "Missing local references"), ("production_without_local_candidate", "Production URLs without local candidates"), ("uncertain_references", "Uncertain references"), ("features", "Forms and other features"), ("classified_external_references", "Classified absolute HTML references")):
        items = result[key]
        lines.extend(["", f"## {title} ({len(items)} distinct)"])
        for item in items[:100]:
            sources = ", ".join(f"`{s}`" for s in item["sources"][:3])
            lines.append(f"- `{item['reference']}` — {item['occurrences']} occurrences; examples: {sources}")
        if len(items) > 100:
            lines.append(f"- ... {len(items) - 100} more; see JSON for the full list.")
    for key, title in (("external_hosts", "External hosts"), ("external_resource_hosts", "External resource or metadata hosts"), ("production_urls", "Absolute production URLs"), ("wordpress_endpoints", "WordPress endpoints")):
        items = result[key]
        lines.extend(["", f"## {title} ({len(items)} distinct)"])
        for item, count in list(items.items())[:100]:
            lines.append(f"- `{item}` — {count}")
        if len(items) > 100:
            lines.append(f"- ... {len(items) - 100} more; see JSON for the full list.")
    lines.extend(["", f"Parse errors: {len(result['parse_errors'])}", "", "## Limitations", result["limitations"], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    for output in (args.json, args.markdown):
        if output.resolve().is_relative_to(root):
            parser.error("Reports must be written outside the audited directory")
    result = audit(root)
    for output in (args.json, args.markdown):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(result), encoding="utf-8")
    print(f"Audited {result['files_total']} files; reports: {args.json}, {args.markdown}")


if __name__ == "__main__":
    main()
