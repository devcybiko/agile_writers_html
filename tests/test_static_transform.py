import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from static_transform import remove_markup, transform_page


class StaticTransformTests(unittest.TestCase):
    def test_removes_search_comments_but_not_author_or_article(self):
        text = '<main><p>Article search and comment words stay.</p><div class="bizberg_user_comment_wrapper"><a>Author</a><div class="bizberg_detail_comment_count">0</div></div><li class="search_wrapper"><div><a>Search</a></div></li><section class="widget_search"><form role="search"><input></form></section><form id="contact"><input></form></main>'
        out, _ = remove_markup(text)
        self.assertIn('Article search and comment words stay.', out)
        self.assertIn('<a>Author</a>', out)
        self.assertIn('id="contact"', out)
        self.assertNotIn('search_wrapper', out)
        self.assertNotIn('widget_search', out)
        self.assertNotIn('bizberg_detail_comment_count', out)

    def test_removes_metadata_and_emoji_loader_without_other_scripts(self):
        text = '<link rel="https://api.w.org/" href="wp-json/index.html"><link rel="stylesheet" href="style.css"><script id="wp-emoji-settings">{}</script><script>document.querySelector("script#wp-emoji-settings")</script><script>keep()</script>'
        out, _ = remove_markup(text)
        self.assertNotIn('wp-json', out)
        self.assertNotIn('wp-emoji-settings', out)
        self.assertIn('style.css', out)
        self.assertIn('keep()', out)

    def test_remove_live_and_local_feed_links(self):
        text = '<link rel="alternate" type="application/rss+xml" href="https://agilewriters.com/category/fantasy/feed/"><link rel="alternate" type="application/rss+xml" href="../../feed/index.html">'
        out, _ = remove_markup(text)
        self.assertNotIn('https://agilewriters.com/category/fantasy/feed/', out)
        self.assertNotIn('../../feed/index.html', out)

    def test_categories_and_archives_use_captured_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            page = root / 'deep' / 'index.html'
            page.parent.mkdir()
            (root / 'category' / 'writing').mkdir(parents=True)
            (root / 'category' / 'writing' / 'index.html').touch()
            (root / '2015').mkdir()
            (root / '2015' / '07.html').touch()
            text = '''<section id="categories-2"><form><select id="cat"><option value="-1">Select</option><option value="22">Writing</option><option value="10">Missing</option></select></form><script>submit()</script></section><select><option value="https://agilewriters.com/2015/07/">July</option><option value="https://agilewriters.com/2015/08/">August</option></select>'''
            out, _, missing = transform_page(text, page, root, {'22': 'writing'})
            self.assertIn('../category/writing/index.html', out)
            self.assertIn('../2015/07.html', out)
            self.assertIn('disabled', out)
            self.assertNotIn('submit()', out)
            self.assertNotIn('agilewriters.com', out)
            self.assertEqual(len(missing), 2)


if __name__ == '__main__':
    unittest.main()
