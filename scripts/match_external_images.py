#!/usr/bin/env python3
"""Find external image src values with matching local candidates in the same srcset."""
import argparse
from collections import defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlsplit


class Images(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and attrs.get('src'):
            self.items.append((attrs['src'], attrs.get('srcset', '')))


def find_matches(root):
    root = root.resolve()
    candidates = defaultdict(set)
    external = defaultdict(set)
    for page in sorted(root.rglob('*.html')):
        parser = Images()
        parser.feed(page.read_text(encoding='utf-8', errors='replace'))
        for source, srcset in parser.items:
            parsed = urlsplit(source)
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                continue
            external[source].add(str(page.relative_to(root)))
            original = Path(unquote(parsed.path)).name.lower()
            if not original:
                continue
            wanted = parse_qs(parsed.query).get('w', [''])[0]
            for part in srcset.split(','):
                pieces = part.strip().split()
                if not pieces:
                    continue
                u = urlsplit(pieces[0])
                if u.scheme or u.netloc or u.query:
                    continue
                target = (page.parent / unquote(u.path)).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    continue
                name = target.name.lower()
                stem = re.sub(r'-\d+x\d+(?=\.[^.]+$)', '', name)
                if name != original and stem != original:
                    continue
                width = pieces[1][:-1] if len(pieces) > 1 and pieces[1].endswith('w') else ''
                rank = 0 if wanted and wanted == width else 1 if name == original else 2
                candidates[source].add((rank, str(target.relative_to(root))))
    matched = {}
    for source, choices in sorted(candidates.items()):
        best = sorted(choices)
        if best and (len(best) == 1 or best[0][0] < best[1][0] or best[0][1] == best[1][1]):
            matched[source] = {'path': best[0][1], 'evidence': 'same image srcset and matching filename', 'pages': sorted(external[source])}
    unmatched = {source: sorted(pages) for source, pages in sorted(external.items()) if source not in matched}
    return {'matched': matched, 'unmatched': unmatched}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.output.resolve().is_relative_to(root):
        parser.error('Output must be outside scanned site')
    result = find_matches(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(f"Matched {len(result['matched'])} external image URLs; {len(result['unmatched'])} need review.")


if __name__ == '__main__':
    main()
