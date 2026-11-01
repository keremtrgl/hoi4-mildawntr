"""Reject the encoding error that makes the game's entire party list blank."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_check import Report, check_files


class ScriptEncodingTests(unittest.TestCase):
    def check_fixture(self, relative_path, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / Path(relative_path).name
            path.write_bytes(data)
            report = Report()
            check_files(report, {relative_path: str(path)})
            return report

    def test_rejects_bom_before_scripted_localisation_comments(self):
        report = self.check_fixture(
            'common/scripted_localisation/parties.txt',
            b'\xef\xbb\xbf# Party names\n# First match wins\n'
            b'defined_text = { name = party_name text = { localization_key = CHP } }\n',
        )
        self.assertEqual(report.count('ERROR'), 1)

    def test_rejects_bom_inside_scripted_localisation(self):
        report = self.check_fixture(
            'common/scripted_localisation/parties.txt',
            b'# Party names\n\xef\xbb\xbfdefined_text = { name = party_name }\n',
        )
        self.assertEqual(report.count('ERROR'), 1)

    def test_accepts_scripted_localisation_without_bom(self):
        report = self.check_fixture(
            'common/scripted_localisation/parties.txt',
            b'# Party names\ndefined_text = { name = party_name text = { localization_key = CHP } }\n',
        )
        self.assertEqual(report.count('ERROR'), 0)

    def test_keeps_yml_bom_requirement(self):
        for prefix, errors in ((b'\xef\xbb\xbf', 0), (b'', 1)):
            with self.subTest(prefix=prefix):
                report = self.check_fixture(
                    'localisation/english/parties_l_english.yml',
                    prefix + b'l_english:\n CHP:0 "CHP"\n',
                )
                self.assertEqual(report.count('ERROR'), errors)

    def test_still_rejects_bom_in_effects_and_triggers(self):
        for folder in ('scripted_effects', 'scripted_triggers'):
            with self.subTest(folder=folder):
                report = self.check_fixture(
                    f'common/{folder}/party.txt', b'\xef\xbb\xbfparty_test = {}\n',
                )
                self.assertEqual(report.count('ERROR'), 1)


if __name__ == '__main__':
    unittest.main()
