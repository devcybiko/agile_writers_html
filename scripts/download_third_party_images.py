#!/usr/bin/env python3
"""Download inventoried image sources for review, retaining provenance and checksums."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BYTES = 10_000_000


class HttpsRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != 'https':
            raise ValueError(f'Redirect to insecure URL rejected: {newurl}')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def image_extension(data):
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith((b'GIF87a', b'GIF89a')):
        return 'gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    raise ValueError('Response is not a recognized JPEG, PNG, GIF, or WebP image')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matches', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    matches = json.loads(args.matches.read_text(encoding='utf-8'))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {'permissions': 'Owner authorized migration download; final redistribution permission or license must be confirmed before deployment.', 'images': [], 'failures': []}
    opener = build_opener(HttpsRedirects())
    for source, pages in sorted(matches['unmatched'].items()):
        parsed = urlsplit(source)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            manifest['failures'].append({'source': source, 'pages': pages, 'error': 'Unsupported source URL'})
            continue
        secure = urlunsplit(('https', parsed.netloc, parsed.path, parsed.query, ''))
        try:
            req = Request(secure, headers={'User-Agent': 'AgileWritersStaticArchive/1.0 (site-owner archival capture)'})
            with opener.open(req, timeout=15) as response:
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ValueError('Image exceeds size limit')
                if not response.headers.get_content_type().startswith('image/'):
                    raise ValueError(f"Unexpected content type: {response.headers.get_content_type()}")
                ext = image_extension(data)
                sha = hashlib.sha256(data).hexdigest()
                filename = f'{sha}.{ext}'
                path = output / filename
                if path.exists():
                    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                        raise ValueError('Existing asset checksum mismatch')
                else:
                    with path.open('xb') as file:
                        file.write(data)
                manifest['images'].append({'source': source, 'retrieved_url': response.url, 'path': filename, 'sha256': sha, 'content_type': response.headers.get_content_type(), 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'pages': pages, 'rights': 'final permission/license pending'})
                print(f'Downloaded {source}', flush=True)
        except (OSError, ValueError) as exc:
            manifest['failures'].append({'source': source, 'pages': pages, 'error': str(exc)})
            print(f'Failed {source}: {exc}', flush=True)
        time.sleep(0.5)
    with (output / 'manifest.json').open('x', encoding='utf-8') as file:
        json.dump(manifest, file, indent=2, ensure_ascii=False)
        file.write('\n')
    print(f"Downloaded {len(manifest['images'])}; failed {len(manifest['failures'])}. Manifest: {output / 'manifest.json'}")


if __name__ == '__main__':
    main()
