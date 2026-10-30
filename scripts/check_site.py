#!/usr/bin/env python3
"""Check captured HTML and CSS links against a local HTTP server."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urldefrag, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from audit_capture import PageParser, SITE_HOSTS, WP_ENDPOINT, classify_file, css_references


class LocalRedirects(HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(urljoin(req.full_url, newurl)).netloc != self.host:
            raise HTTPError(newurl, code, "External redirect blocked", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check(root, base):
    root = root.resolve()
    base = base.rstrip("/") + "/"
    parsed_base = urlsplit(base)
    if parsed_base.scheme not in ("http", "https") or parsed_base.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Base URL must use a loopback HTTP server")
    opener = build_opener(LocalRedirects(parsed_base.netloc))
    urls = defaultdict(set)
    production = Counter()
    endpoints = Counter()
    external_resources = Counter()
    external_links = Counter()
    metadata = Counter()
    excluded = Counter()
    scripts_with_endpoint = set()
    expected_types = defaultdict(set)
    files = sorted(p for p in root.rglob("*") if p.is_file() and classify_file(p) in ("html", "css"))
    for path in files:
        relative = path.relative_to(root).as_posix()
        # Captured filenames may contain literal URL delimiters.
        source_url = urljoin(base, quote(relative, safe="/"))
        text = path.read_text(encoding="utf-8", errors="replace")
        if classify_file(path) == "html":
            page = PageParser()
            page.feed(text)
            refs = page.references + [r for css in page.inline_css for r in css_references(css)]
            for feature, detail in page.features:
                if feature == 'search input' or (feature == 'possible search/comment markup' and any(x in detail.lower() for x in ('search-form', 'widget_search', 'search_wrapper', 'comment-respond', 'comments-area', 'comment_count'))):
                    excluded[feature + ': ' + detail] += 1
            for category, ref in page.classified:
                parsed_ref = urlsplit(ref)
                if parsed_ref.netloc and parsed_ref.netloc != parsed_base.netloc:
                    if category == 'navigation':
                        external_links[ref] += 1
                    elif category == 'metadata':
                        metadata[ref] += 1
                    elif category == 'resource':
                        external_resources[ref] += 1
            for script in re.findall(r'<script\b[^>]*>(.*?)</script\s*>', text, re.I | re.S):
                if re.search(r'(?:wp-json|wp-admin|wp-login\.php|wp-comments-post\.php|xmlrpc\.php)', script, re.I):
                    scripts_with_endpoint.add(relative)
        else:
            refs = css_references(text)
        urls[source_url].add(relative)
        for context, ref in refs:
            ref = ref.strip()
            if not ref or ref.startswith("#"):
                continue
            parsed = urlsplit(ref)
            if WP_ENDPOINT.search(ref):
                endpoints[ref] += 1
            if parsed.hostname and parsed.hostname.lower() in SITE_HOSTS:
                production[ref] += 1
            if parsed.netloc and context == 'css':
                external_resources[ref] += 1
            if parsed.scheme and parsed.scheme not in ("http", "https"):
                continue
            resolved = urldefrag(urljoin(source_url, ref))[0]
            if urlsplit(resolved).netloc == parsed_base.netloc:
                urls[resolved].add(relative)
                if context.startswith('script[src]'):
                    expected_types[resolved].add('javascript')
                elif context == 'css' and urlsplit(resolved).path.lower().endswith('.css'):
                    expected_types[resolved].add('css')
                elif context == 'link[href]' and ('.css' in urlsplit(resolved).path.lower()):
                    expected_types[resolved].add('css')

    failures = []
    successes = 0
    content_types = Counter()
    mime_errors = []
    for url, sources in sorted(urls.items()):
        try:
            with opener.open(Request(url, method="GET"), timeout=10) as response:
                status = response.status
                mime = response.headers.get_content_type()
                content_types[mime] += 1
                for expected in expected_types[url]:
                    allowed = {'text/javascript', 'application/javascript', 'application/x-javascript'} if expected == 'javascript' else {'text/css'}
                    if mime not in allowed:
                        mime_errors.append((url, expected, mime))
                if 200 <= status < 400:
                    successes += 1
                else:
                    failures.append((url, str(status), sorted(sources)[:5]))
        except (HTTPError, URLError, OSError, ValueError) as exc:
            failures.append((url, str(exc), sorted(sources)[:5]))
    return len(files), len(urls), successes, failures, production, endpoints, content_types, mime_errors, external_resources, external_links, metadata, excluded, scripts_with_endpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not (args.root / "index.html").is_file():
        parser.error("Root must contain index.html")
    if args.report.resolve().is_relative_to(args.root.resolve()):
        parser.error("Report must be outside the site directory")
    try:
        files, total, successes, failures, production, endpoints, types, mime_errors, resources, links, metadata, excluded, scripts_with_endpoint = check(args.root, args.base_url)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Check failed: {exc}\n")
    lines = ["# Local HTTP verification", "", f"- Root: `{args.root.resolve()}`", f"- Base: `{args.base_url}`", f"- HTML/CSS files inspected: {files}", f"- Unique local URLs checked: {total}", f"- Successful responses: {successes}", f"- Failed responses: {len(failures)}", f"- Distinct absolute production URLs: {len(production)}", f"- Distinct WordPress endpoint references: {len(endpoints)}", "", "## Failed local requests"]
    for url, error, sources in failures:
        lines.append(f"- `{url}` — {error}; referenced by {', '.join('`' + s + '`' for s in sources)}")
    if not failures:
        lines.append("- None detected.")
    lines += ['', '## Script and stylesheet content types', f'- Incorrect MIME types: {len(mime_errors)}']
    lines += [f'- `{url}` — expected {expected}, received `{actual}`' for url, expected, actual in mime_errors]
    for title, values in (('External resource references', resources), ('Ordinary external links', links), ('External metadata', metadata), ('Search/comment indicators', excluded)):
        lines += ['', f'## {title} ({len(values)} distinct)']
        lines += [f'- `{value}` — {count}' for value, count in values.most_common(50)]
        if len(values) > 50:
            lines.append(f'- ... {len(values) - 50} more; see site audit.')
    lines += ['', f'## HTML files with possible inline WordPress/PHP endpoint references ({len(scripts_with_endpoint)})']
    lines += [f'- `{path}`' for path in sorted(scripts_with_endpoint)[:50]]
    lines += ["", "## Response content types"] + [f"- `{k}`: {v}" for k, v in types.most_common()]
    lines += ["", "## Limitations", "", "GET checks cover statically discoverable HTML and CSS references only; external URLs are not requested. Search/comment detection and inline endpoint detection are heuristic; CSS class names, dynamically generated requests, JavaScript files, carousel interactions, visual fidelity, and deployment routing require separate review. HTTP success does not prove a response contains the intended content.", ""]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Checked {total} URLs: {successes} successful, {len(failures)} failed, {len(mime_errors)} MIME errors; {len(resources)} external resource references. Report: {args.report}")
    if failures or mime_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
