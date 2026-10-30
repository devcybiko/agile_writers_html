#!/usr/bin/env python3
"""Download explicitly approved assets and record checksums in a manifest."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
ALLOWED_HOSTS = {'fonts.googleapis.com', 'fonts.gstatic.com', 'raw.githubusercontent.com'}
MAX_BYTES = 5_000_000


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError('Redirect to unapproved host')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--download', action='store_true')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    data = json.loads(manifest.read_text(encoding='utf-8'))
    errors = []
    for item in data['assets']:
        path = (manifest.parent / item['path']).resolve()
        url = urlsplit(item['url'])
        if not path.is_relative_to(manifest.parent / 'vendor') or url.scheme != 'https' or url.hostname not in ALLOWED_HOSTS:
            errors.append(f"Invalid path or URL: {item['url']}")
            continue
        if not item.get('approved'):
            print(f"Not approved; skipped: {item['url']}")
            continue
        if args.download and not path.exists():
            try:
                request = Request(item['url'], headers={'User-Agent': AGENT})
                with build_opener(SafeRedirect()).open(request, timeout=30) as response:
                    final = urlsplit(response.url)
                    if final.scheme != 'https' or final.hostname not in ALLOWED_HOSTS:
                        raise ValueError('Redirect to unapproved host')
                    content_type = response.headers.get_content_type()
                    if content_type not in item['expected_types']:
                        raise ValueError(f'Unexpected content type {content_type}')
                    content = response.read(MAX_BYTES + 1)
                    if len(content) > MAX_BYTES:
                        raise ValueError('Asset exceeds size limit')
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(content)
                item.update(content_type=content_type, sha256=hashlib.sha256(content).hexdigest(), retrieved_at=datetime.now(timezone.utc).isoformat())
                print(f'Downloaded {item["path"]}')
            except (OSError, ValueError) as exc:
                errors.append(f"{item['url']}: {exc}")
        elif path.exists():
            actual = digest(path)
            if item.get('sha256') != actual:
                errors.append(f'Checksum missing or mismatch: {path}')
            else:
                print(f'Verified {item["path"]}')
        elif args.verify:
            errors.append(f'Missing: {path}')
        else:
            print(f'Pending: {item["path"]}')
    if args.download:
        manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for error in errors:
        print('ERROR:', error)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
