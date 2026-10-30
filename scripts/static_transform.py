"""Targeted static-only transformations, applied only to generated builds."""
from collections import Counter
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import quote, urlsplit


VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
REMOVE_CLASSES = {'search_wrapper', 'widget_search', 'full-screen-search', 'bizberg_detail_comment_count', 'comments-area', 'comment-respond'}


class Removals(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.offsets = [0]
        for m in re.finditer('\n', text):
            self.offsets.append(m.end())
        self.stack = []
        self.ranges = []

    def absolute_offset(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.absolute_offset()
        raw = self.get_starttag_text()
        attrs = dict(attrs)
        classes = set((attrs.get('class') or '').split())
        identifier = attrs.get('id') or ''
        remove = bool(classes & REMOVE_CLASSES or identifier in {'comments', 'respond', 'wp-emoji-settings'})
        if tag == 'form' and (attrs.get('role') == 'search' or 'search-form' in classes):
            remove = True
        if tag == 'link':
            rel = (attrs.get('rel') or '').lower()
            href = (attrs.get('href') or '').lower()
            remove = ('api.w.org' in rel or rel in {'edituri', 'shortlink'} or 'wp-json/' in href or 'xmlrpc.php' in href)
            # Feed publication is out of scope; remove local and remote discovery links.
            if (attrs.get('type') or '').lower() in {'application/rss+xml', 'application/atom+xml'}:
                remove = True
        if tag == 'meta' and (attrs.get('name') or '').lower() == 'generator' and 'wordpress' in (attrs.get('content') or '').lower():
            remove = True
        if tag == 'script' and (identifier.startswith('contact-form-7-') or 'contact-form-7/' in (attrs.get('src') or '')):
            remove = True
        if tag in VOID or raw.rstrip().endswith('/>'):
            if remove:
                self.ranges.append((start, start + len(raw)))
        else:
            self.stack.append((tag, start, remove))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                entries = self.stack[i:]
                del self.stack[i:]
                end = self.text.find('>', self.absolute_offset()) + 1
                if end <= 0:
                    raise ValueError('Unterminated HTML end tag')
                for _, start, remove in entries:
                    if remove:
                        self.ranges.append((start, end))
                break


def remove_markup(text):
    parser = Removals(text)
    parser.feed(text)
    for _, _, remove in parser.stack:
        if remove:
            raise ValueError('Unclosed targeted HTML element')
    merged = []
    for start, end in sorted(parser.ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    for start, end in reversed(merged):
        text = text[:start] + text[end:]
    # Emoji loader is an anonymous inline script; native emoji remain in text.
    text, n = re.subn(r'<script\b[^>]*>(?:(?!</script>).)*wp-emoji-settings(?:(?!</script>).)*</script\s*>', '', text, flags=re.I | re.S)
    return text, len(merged) + n


def categories(root):
    result = {}
    for path in (root / 'wp-json/wp/v2/categories').glob('*'):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            result[str(data['id'])] = data['slug']
        except (ValueError, KeyError, OSError):
            continue
    return result


def relative_url(page, target):
    return quote(os.path.relpath(target, page.parent), safe='/')


def transform_page(text, page, root, category_map):
    text, removed = remove_markup(text)
    unavailable = set()
    widget = re.compile(r'(<section\b[^>]*\bid=["\']categories-2["\'][^>]*>)(.*?)(</section\s*>)', re.I | re.S)
    def replace_categories(match):
        body = match.group(2)
        select = re.search(r'<select\b[^>]*\bid=["\']cat["\'][^>]*>.*?</select\s*>', body, re.I | re.S)
        if not select:
            raise ValueError(f'Category widget has no expected select: {page}')
        options = []
        for value, label in re.findall(r'<option\b[^>]*\bvalue=["\']([^"\']+)["\'][^>]*>(.*?)</option\s*>', select.group(), re.I | re.S):
            if value == '-1':
                options.append('<option value="">Select Category</option>')
                continue
            slug = category_map.get(value)
            target = root / 'category' / slug / 'index.html' if slug else None
            if target and target.is_file():
                options.append(f'<option value="{relative_url(page, target)}">{label}</option>')
            else:
                unavailable.add(f'category {value}: {html.unescape(re.sub("<[^>]+>", "", label)).strip()}')
                options.append(f'<option value="" disabled>{label} (unavailable)</option>')
        return match.group(1) + '<h2 class="widget-title">Categories</h2><label class="screen-reader-text" for="static-categories">Categories</label><select id="static-categories" onchange="if(this.value)location.href=this.value">' + ''.join(options) + '</select>' + match.group(3)
    text, widgets = widget.subn(replace_categories, text)
    # Preserve the archive dropdown; direct each captured month to its local HTML file.
    option = re.compile(r'(<option\b[^>]*\bvalue=["\'])(https?://(?:www\.)?agilewriters\.com/(\d{4})/(\d{2})/)(["\'][^>]*>)', re.I)
    def replace_archive(match):
        target = root / match.group(3) / (match.group(4) + '.html')
        if target.is_file():
            return match.group(1) + relative_url(page, target) + match.group(5)
        unavailable.add('archive ' + match.group(3) + '/' + match.group(4))
        return match.group(1) + '' + match.group(5)[:-1] + ' disabled>'
    text, archive_count = option.subn(replace_archive, text)
    return text, {'removed': removed, 'category_widgets': widgets, 'archive_options': archive_count}, unavailable
