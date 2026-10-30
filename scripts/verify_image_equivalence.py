#!/usr/bin/env python3
"""Compare public image bytes with same-named captured files; never save downloads."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOSTS = {'agilewriter.files.wordpress.com', 'agilewriter.wordpress.com', 'theagilewriter.com'}
LIMIT = 5_000_000


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != 'https' or target.hostname not in HOSTS:
            raise ValueError(f'Unexpected redirect destination: {newurl}')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('matches', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    result = json.loads(args.matches.read_text(encoding='utf-8'))
    index = defaultdict(list)
    for path in root.rglob('*'):
        if path.is_file():
            index[path.name.lower()].append(path)
    checks = []
    for url, pages in list(result['unmatched'].items()):
        parsed = urlsplit(url)
        if parsed.hostname not in HOSTS:
            continue
        candidates = index.get(Path(unquote(parsed.path)).name.lower(), [])
        if not candidates:
            continue
        safe_url = urlunsplit(('https', parsed.netloc, parsed.path, parsed.query, ''))
        try:
            with build_opener(SafeRedirect()).open(Request(safe_url, headers={'User-Agent': 'AgileWritersStaticArchive/1.0 (site-owner archival comparison)'}), timeout=15) as response:
                final = urlsplit(response.url)
                if final.scheme != 'https' or final.hostname not in HOSTS:
                    raise ValueError(f'Unexpected redirect destination: {response.url}')
                content = response.read(LIMIT + 1)
                if len(content) > LIMIT or not response.headers.get_content_type().startswith('image/'):
                    raise ValueError('Response is oversized or not an image')
            sha = hashlib.sha256(content).hexdigest()
            matched = [p for p in candidates if hashlib.sha256(p.read_bytes()).hexdigest() == sha]
            if len(matched) == 1:
                result['matched'][url] = {'path': str(matched[0].relative_to(root)), 'evidence': 'byte-identical to HTTPS source', 'sha256': sha, 'pages': pages}
                del result['unmatched'][url]
            checks.append({'url': url, 'matches': len(matched), 'sha256': sha})
        except (OSError, ValueError) as exc:
            checks.append({'url': url, 'error': str(exc)})
        time.sleep(1)
    result['comparison_checks'] = checks
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(f"Compared {len(checks)} URLs; {len(result['matched'])} total matches, {len(result['unmatched'])} unresolved.")


if __name__ == '__main__':
    main()
