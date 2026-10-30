#!/usr/bin/env python3
"""Create a new static-site build from an existing, unmodified wget capture."""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

from audit_capture import SITE_HOSTS, audit, classify_file, local_candidates
from static_transform import categories, transform_page


SCRIPT_SRC = re.compile(rb'(<script\b[^>]*?\bsrc\s*=\s*)(["\'])([^"\']+)(\2)', re.I)
IMG_SRC = re.compile(r'(<img\b[^>]*?(?<![-\w])src\s*=\s*)(["\'])([^"\']+)(\2)', re.I)
HTML_URL = re.compile(r'((?<![-\w])(?:href|src|poster)\s*=\s*)(["\'])([^"\']+)(\2)', re.I)


def add_supplement(output, supplement):
    supplement = supplement.resolve()
    root = supplement / 'agilewriters.com'
    mapping = json.loads((supplement / 'category-map.json').read_text(encoding='utf-8'))
    pages = []
    copied = 0
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError(f'Supplement contains a symbolic link: {path}')
        target = output / path.relative_to(root)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
        if target.suffix == '.html':
            pages.append(target)
    if len([p for p in pages if 'category' in p.relative_to(output).parts]) < len(mapping):
        raise ValueError('Supplement is missing one or more category pages')
    for page in pages:
        text = page.read_text(encoding='utf-8')
        def rewrite(match):
            ref = html.unescape(match.group(3))
            parsed = urlsplit(ref)
            if (parsed.hostname or '').lower() not in SITE_HOSTS:
                return match.group(0)
            local = parsed.path or '/'
            if parsed.query:
                local += '?' + parsed.query
            candidates = [p for p in local_candidates(output, page, local) if p.is_file()]
            if not candidates:
                return match.group(0)
            ref = quote(os.path.relpath(candidates[0], page.parent), safe='/')
            if parsed.fragment:
                ref += '#' + parsed.fragment
            return match.group(1) + match.group(2) + ref + match.group(4)
        page.write_text(HTML_URL.sub(rewrite, text), encoding='utf-8')
    return mapping, copied, pages


def localize_verified_images(output):
    asset_root = Path(__file__).resolve().parent.parent / 'assets'
    manifest = asset_root / 'image-matches.json'
    matches = json.loads(manifest.read_text(encoding='utf-8'))['matched']
    third_party = asset_root / 'third-party-20261029'
    if (third_party / 'manifest.json').is_file():
        downloaded = json.loads((third_party / 'manifest.json').read_text(encoding='utf-8'))
        dest_dir = output / 'assets/third-party-20261029'
        if dest_dir.exists():
            raise FileExistsError(f'Build already contains third-party assets: {dest_dir}')
        dest_dir.mkdir(parents=True)
        shutil.copy2(third_party / 'manifest.json', dest_dir / 'manifest.json')
        for entry in downloaded['images']:
            source = (third_party / entry['path']).resolve()
            if not source.is_relative_to(third_party.resolve()) or hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError(f'Third-party asset checksum mismatch: {source}')
            dest = dest_dir / entry['path']
            if not dest.exists():
                shutil.copy2(source, dest)
            matches[entry['source']] = {'path': str(dest.relative_to(output)), 'pages': entry['pages']}
    changes = []
    for page in sorted(output.rglob('*.html')):
        original = page.read_text(encoding='utf-8')
        relative_page = str(page.relative_to(output))
        count = [0]
        def replace(match):
            entry = matches.get(html.unescape(match.group(3)))
            if not entry or relative_page not in entry['pages']:
                return match.group(0)
            target = (output / entry['path']).resolve()
            if not target.is_relative_to(output) or not target.is_file():
                raise ValueError(f'Matched image missing from build: {target}')
            count[0] += 1
            local = quote(os.path.relpath(target, page.parent), safe='/')
            return match.group(1) + match.group(2) + local + match.group(4)
        updated = IMG_SRC.sub(replace, original)
        if count[0]:
            page.write_text(updated, encoding='utf-8')
            changes.append((relative_page, count[0]))
    return changes


def remove_missing_theme_references(output):
    """Remove missing, unused font sources and unavailable theme image URLs."""
    css_dir = output / 'wp-content/themes/bizberg/assets/css'
    changes = []
    for filename, family in (('main.css?ver=1.0.css', 'Aclonica'), ('component.css?ver=1.0.css', 'slick')):
        path = css_dir / filename
        text = path.read_text(encoding='utf-8')
        pattern = re.compile(r'@font-face\s*\{(?=[^}]*font-family\s*:\s*[\'"]' + re.escape(family) + r'[\'"])[^}]*\}', re.I)
        text, count = pattern.subn('', text)
        if count != 1:
            raise ValueError(f'Expected one {family} font declaration, found {count}')
        path.write_text(text, encoding='utf-8')
        changes.append(f'{path.relative_to(output)}: removed unused {family} font declaration')
    path = css_dir / 'style.css?ver=1.0.css'
    text = path.read_text(encoding='utf-8')
    pattern = re.compile(r'url\(\s*[\'"]?https://agilewriters\.com/wp-content/themes/bizberg/assets/(?:images|img)/[^)\'"]+[\'"]?\s*\)', re.I)
    text, count = pattern.subn('none', text)
    if count != 13:
        raise ValueError(f'Expected 13 missing theme image references, found {count}')
    path.write_text(text, encoding='utf-8')
    changes.append(f'{path.relative_to(output)}: replaced {count} unavailable image URLs with none; retained other CSS')
    external_url = "url('http://wp3.commonsupport.com/newwp/borvel/wp-content/uploads/2018/07/6-1.jpg')"
    if text.count(external_url) != 1:
        raise ValueError('Expected one unused external footer background')
    path.write_text(text.replace(external_url, 'none'), encoding='utf-8')
    changes.append(f'{path.relative_to(output)}: removed unavailable external footer background (no footer_pro markup in captured pages)')
    return changes


def localize_assets(output):
    """Copy verified Lato resources and replace identified captured dependencies."""
    asset_root = Path(__file__).resolve().parent.parent / 'assets'
    manifest = json.loads((asset_root / 'manifest.json').read_text(encoding='utf-8'))
    vendor = output / 'assets' / 'vendor'
    if vendor.exists():
        raise FileExistsError(f'Build already contains vendor directory: {vendor}')
    assets = [item for item in manifest['assets'] if item.get('approved')]
    for item in assets:
        src = asset_root / item['path']
        if hashlib.sha256(src.read_bytes()).hexdigest() != item.get('sha256'):
            raise ValueError(f'Asset checksum mismatch: {src}')
        dest = output / 'assets' / item['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    css = output / 'assets/vendor/lato/lato.css'
    data = css.read_text(encoding='utf-8')
    for item in assets:
        if item['path'].endswith('.woff2'):
            data = data.replace(item['url'], Path(item['path']).name)
    if 'https://fonts.gstatic.com/' in data:
        raise ValueError('Lato stylesheet contains an unmanifested font URL')
    css.write_text(data, encoding='utf-8')
    replacements = {
        'https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&amp;display=swap': output / 'assets/vendor/lato/lato.css',
        'https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap': output / 'assets/vendor/lato/lato.css',
        'https://bizbergthemes.com/omg-blog-lite/wp-content/themes/bizberg/assets/images/breadcrum.jpg': output / 'wp-content/themes/bizberg/assets/images/breadcrum.jpg',
        'https://agilewriters.com/wp-content/uploads/2017/08/225x225bb.jpg.pagespeed.ce.gPi9OVWGR6.jpg': output / 'wp-content/uploads/2017/08/225x225bb.jpg',
    }
    if not all(p.is_file() for p in replacements.values()):
        raise ValueError('An expected captured replacement asset is missing')
    changes = []
    for page in sorted(output.rglob('*')):
        if not page.is_file() or not (page.name.endswith('.html') or page.name.endswith('.css')) or page == css:
            continue
        raw = page.read_bytes()
        updated = raw
        count = 0
        for source, target in replacements.items():
            needle = source.encode('utf-8')
            occurrences = updated.count(needle)
            if occurrences:
                relative = quote(os.path.relpath(target, page.parent), safe='/')
                updated = updated.replace(needle, relative.encode('ascii'))
                count += occurrences
        if count:
            page.write_bytes(updated)
            changes.append((str(page.relative_to(output)), count))
    return changes


def fix_script_mime(output):
    """Add .js aliases for wget filenames whose final suffix is a query value."""
    changed = []
    aliases = set()
    for page in sorted(output.rglob("*.html")):
        original = page.read_bytes()
        replacements = [0]

        def replace(match):
            ref = match.group(3).decode("ascii", errors="ignore")
            parsed = urlsplit(ref)
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                return match.group(0)
            decoded = unquote(parsed.path)
            if ".js?" not in decoded.lower():
                return match.group(0)
            target = (output / decoded.lstrip("/")) if decoded.startswith("/") else (page.parent / decoded)
            target = target.resolve()
            if not target.is_relative_to(output.resolve()) or not target.is_file():
                return match.group(0)
            alias = target.with_name(target.name + ".js")
            if alias.exists() and alias not in aliases:
                raise FileExistsError(f"Script alias already exists: {alias}")
            if alias not in aliases:
                shutil.copy2(target, alias)
                aliases.add(alias)
            replacements[0] += 1
            return match.group(1) + match.group(2) + match.group(3) + b".js" + match.group(4)

        updated = SCRIPT_SRC.sub(replace, original)
        if replacements[0]:
            page.write_bytes(updated)
            changed.append((str(page.relative_to(output)), replacements[0]))
    return changed, aliases


def build(capture, output, report, supplement=None):
    capture = capture.resolve()
    output = output.resolve()
    report = report.resolve()
    source = capture / "agilewriters.com" if (capture / "agilewriters.com").is_dir() else capture
    if not (source / "index.html").is_file():
        raise ValueError(f"No homepage index.html found in {source}")
    if output == capture or output.is_relative_to(capture) or capture.is_relative_to(output):
        raise ValueError("Capture and output directories must not contain one another")
    if report.is_relative_to(capture) or report.is_relative_to(output):
        raise ValueError("Report must be outside the capture and output directories")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if report.exists() or report.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing report: {report}")

    output.parent.mkdir(parents=True, exist_ok=True)
    # copytree creates the destination itself and fails if it already exists.
    shutil.copytree(source, output, symlinks=True)
    supplement_map, supplement_count, supplement_pages = add_supplement(output, supplement) if supplement else ({}, 0, [])
    localized = localize_assets(output)
    missing_theme_changes = remove_missing_theme_references(output)
    category_map = categories(output)
    category_map.update(supplement_map)
    transformed = []
    unavailable = set()
    for page in sorted(output.rglob('*.html')):
        original = page.read_text(encoding='utf-8')
        updated, counts, missing = transform_page(original, page, output, category_map)
        if updated != original:
            page.write_text(updated, encoding='utf-8')
            transformed.append((str(page.relative_to(output)), counts))
        unavailable.update(missing)
    image_changes = localize_verified_images(output)
    changed, aliases = fix_script_mime(output)
    removed_feeds = []
    for feed in sorted(p for p in output.rglob('*.html') if p.is_file() and classify_file(p) == 'feed'):
        removed_feeds.append(str(feed.relative_to(output)))
        feed.unlink()
    result = audit(output)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Static build report", "",
        f"- Source: `{source}`", f"- Build: `{output}`",
        f"- Files copied: {result['files_total']}",
        f"- Supplemental capture: {supplement or 'none'}; copied {supplement_count} additional files ({len(supplement_pages)} HTML pages).",
        f"- Script MIME fix: added {len(aliases)} `.js` aliases and updated script references in {len(changed)} HTML files. Original captured files remain in the build.",
        f"- Localized Lato, a captured Bizberg background, and the original Structure category image in {len(localized)} HTML/CSS files; Lato license included.",
        "- Removed unused missing Aclonica and Slick font declarations and replaced 13 unavailable theme image URLs with CSS `none`.",
        f"- Applied targeted static-only HTML transformations to {len(transformed)} files; unavailable archive/category choices are disabled and listed below.",
        f"- Localized verified image matches and authorized downloaded third-party images in {len(image_changes)} HTML files; final third-party permissions must be confirmed before deployment.",
        f"- Removed {len(removed_feeds)} RSS/Atom snapshots from this build and their HTML discovery links; retained capture files unchanged.",
        "- Existing wget link conversions and other assets were retained.",
        "", "## Unresolved items", "",
        f"- {len(result['production_without_local_candidate'])} distinct production references have no local candidate; these need review.",
        f"- {len(result['external_resource_hosts'])} external resource or metadata hosts appear in HTML/CSS; review actual browser requests.",
        f"- {len(result['wordpress_endpoints'])} distinct WordPress endpoint references remain; some are metadata, others may support runtime features.",
        "- Search/comment controls and WordPress metadata were targeted for removal; review remaining content and runtime behavior.",
        "- JavaScript-generated URLs, forms, carousel behavior, and browser compatibility have not been verified.",
        "- Test script MIME handling on the intended deployment host; other unusual wget filenames remain.",
        "- The site has not been visually validated or approved for deployment.", "",
        "See the site audit for details. Static parsing does not prove completeness or functionality.", "",
        "## Changed HTML files", "",
    ]
    lines.extend(f"- `{path}`: {count} script references" for path, count in changed)
    if not changed:
        lines.append("- None.")
    lines += ["", "## Added script aliases", ""]
    lines.extend(f"- `{path.relative_to(output)}`" for path in sorted(aliases))
    if not aliases:
        lines.append("- None.")
    lines += ["", "## Files with localized references", ""]
    lines.extend(f"- `{path}`: {count} replacements" for path, count in localized)
    lines += ["", "## Missing theme reference changes", ""]
    lines.extend(f"- `{entry}`" for entry in missing_theme_changes)
    lines += ["", "## Removed feed snapshots", ""]
    lines.extend(f"- `{path}`" for path in removed_feeds)
    lines += ["", "## Static HTML transformations", ""]
    lines.extend(f"- `{path}`: {counts}" for path, counts in transformed)
    lines += ["", "## Localized image src references", ""]
    lines.extend(f"- `{path}`: {count} references" for path, count in image_changes)
    lines += ["", "## Unavailable category and archive choices", ""]
    lines.extend(f"- {item}" for item in sorted(unavailable))
    if not unavailable:
        lines.append('- None detected.')
    lines.append("")
    # Exclusive creation avoids silently replacing a report from another build.
    with report.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print(f"Copied {result['files_total']} files to {output}; report: {report}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--supplement", type=Path)
    args = parser.parse_args()
    try:
        build(args.capture, args.output, args.report, args.supplement)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Build failed: {exc}\n")


if __name__ == "__main__":
    main()
