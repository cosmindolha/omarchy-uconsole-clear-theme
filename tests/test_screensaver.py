from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/'gui/uconsole-screensaver'


class ScreensaverTests(unittest.TestCase):
    def test_missing_renderer_exits_immediately(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(['/bin/bash', str(SCRIPT)], env=dict(os.environ, PATH=temp),
                                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 1)
            self.assertIn('ttfx is not installed', result.stderr)

    def test_failed_renderer_is_not_restarted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            counter = root/'runs'
            fake = root/'ttfx'
            fake.write_text('#!/bin/sh\necho run >> "$RUN_COUNTER"\nexit 7\n')
            fake.chmod(0o755)
            hypr = root/'hyprctl'
            hypr.write_text('#!/bin/sh\necho \'{"class":"org.omarchy.screensaver"}\'\n')
            hypr.chmod(0o755)
            # Only the focus predicate is stubbed; exercise the actual runner loop.
            jq = root/'jq'
            jq.write_text('#!/bin/sh\ncat >/dev/null\nexit 0\n')
            jq.chmod(0o755)
            result = subprocess.run(['/bin/bash', str(SCRIPT)],
                                    env=dict(os.environ, PATH=str(root)+':/usr/bin:/bin', RUN_COUNTER=str(counter)),
                                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 7)
            self.assertEqual(counter.read_text().splitlines(), ['run'])
            self.assertIn('renderer exited with status 7', result.stderr)
