"""Catch Millennium Dawn updates that leave the language pack's translations stale."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import md_loc


class MdLocCompareTests(unittest.TestCase):
    def setUp(self):
        md_only = md_loc.pack_keys() - md_loc.mod_keys()
        self.key = sorted(md_only)[0]
        self.file = 'localisation/english/replace/test_l_english.yml'

    def compare(self, lines):
        with tempfile.TemporaryDirectory() as md:
            path = Path(md) / self.file
            path.parent.mkdir(parents=True)
            path.write_text('l_english:\n' + ''.join(f' {k}:0 "{v}"\n' for k, v in lines.items()), encoding='utf-8-sig')
            base = {'md_version': 'test', 'files': [self.file], 'lines': {self.key: md_loc.fingerprint('Old text')}}
            return md_loc.compare(md, base)

    def test_unchanged_english_is_clean(self):
        self.assertEqual(self.compare({self.key: 'Old text'}), ([], []))

    def test_reports_changed_english_of_a_translated_line(self):
        changed, new = self.compare({self.key: 'New text'})
        self.assertEqual([k for k, _, _ in changed], [self.key])
        self.assertEqual(new, [])

    def test_reports_new_untranslated_line_in_a_covered_file(self):
        changed, new = self.compare({self.key: 'Old text', 'zz_md_loc_test_new_key': 'Brand new'})
        self.assertEqual(changed, [])
        self.assertEqual([k for k, _, _ in new], ['zz_md_loc_test_new_key'])


if __name__ == '__main__':
    unittest.main()
