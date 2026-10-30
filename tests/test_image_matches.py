import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from match_external_images import find_matches


class ImageMatchTests(unittest.TestCase):
    def test_same_srcset_and_width_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'photo.jpg').touch()
            (root / 'photo-300x200.jpg').touch()
            (root / 'other.jpg').touch()
            (root / 'index.html').write_text('<img src="https://example.org/photo.jpg?w=300" srcset="photo.jpg 600w, photo-300x200.jpg 300w"><img src="https://example.org/unrelated.jpg" srcset="other.jpg 300w">')
            result = find_matches(root)
            self.assertEqual(result['matched']['https://example.org/photo.jpg?w=300']['path'], 'photo-300x200.jpg')
            self.assertIn('https://example.org/unrelated.jpg', result['unmatched'])


if __name__ == '__main__':
    unittest.main()
