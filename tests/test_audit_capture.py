import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_capture import classify_file


class AuditTests(unittest.TestCase):
    def test_feed_snapshot_is_not_html(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'index.html'
            path.write_text('<?xml version="1.0"?><rss version="2.0"><channel/></rss>')
            self.assertEqual(classify_file(path), 'feed')
            path.write_text('<!doctype html><html></html>')
            self.assertEqual(classify_file(path), 'html')


if __name__ == '__main__':
    unittest.main()
