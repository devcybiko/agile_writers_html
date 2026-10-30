import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_static import add_supplement


class SupplementTests(unittest.TestCase):
    def test_copy_and_rewrite_captured_internal_links(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            output = root / 'output'
            output.mkdir()
            (output / 'index.html').write_text('original')
            source = root / 'supplement'
            (source / 'agilewriters.com/category/fantasy').mkdir(parents=True)
            (source / 'category-map.json').write_text(json.dumps({'39': 'fantasy'}))
            (source / 'agilewriters.com/category/fantasy/index.html').write_text('<a href="https://agilewriters.com/">Home</a>')
            (source / 'agilewriters.com/index.html').write_text('must not overwrite')
            mapping, count, pages = add_supplement(output, source)
            self.assertEqual(mapping['39'], 'fantasy')
            self.assertEqual(count, 1)
            self.assertEqual((output / 'index.html').read_text(), 'original')
            self.assertIn('href="../../index.html"', pages[0].read_text())


if __name__ == '__main__':
    unittest.main()
