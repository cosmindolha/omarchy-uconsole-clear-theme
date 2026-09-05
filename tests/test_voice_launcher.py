import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('launcher_match',Path(__file__).parents[1]/'gui/launcher_match.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class VoiceMatches(unittest.TestCase):
    def setUp(self):
        self.apps=[{'id':'foot.desktop','name':'Foot'},{'id':'org.gnome.Nautilus.desktop','name':'Files'},
                   {'id':'chromium.desktop','name':'Chromium'},{'id':'btop.desktop','name':'btop++'}]
    def test_english_and_romanian_aliases(self):
        for query,want in [('please open terminal','foot.desktop'),('deschide fișiere','org.gnome.Nautilus.desktop'),
                           ('launch chromium','chromium.desktop'),('open bee top','btop.desktop')]:
            self.assertEqual(m.match_apps(query,self.apps)[1],want)
    def test_no_arbitrary_command(self):
        for text in ['rm -rf /home','shutdown now','launch madeupapp','']:
            self.assertIsNone(m.match_apps(text,self.apps)[1])
    def test_duplicate_names_require_choice(self):
        apps=[{'id':'one.desktop','name':'Terminal'},{'id':'two.desktop','name':'Terminal'}]
        results,auto=m.match_apps('open terminal',apps)
        self.assertEqual(len(results),2);self.assertIsNone(auto)
    def test_alias_cannot_launch_missing_app(self):
        self.assertIsNone(m.match_apps('open terminal',[])[1])
