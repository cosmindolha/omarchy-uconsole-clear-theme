#!/usr/bin/python3
"""List and launch visible desktop applications through GIO, never a spoken shell command."""
import json
from pathlib import Path
import subprocess
import sys
from gi.repository import Gio

apps = {a.get_id(): a for a in Gio.AppInfo.get_all() if a.should_show() and a.get_id()}
if len(sys.argv) == 3 and sys.argv[1] == '--launch':
    app = apps.get(sys.argv[2])
    if app is None:
        raise SystemExit('App is no longer installed')
    if app.get_id() == 'btop.desktop' and (Path.home()/'.local/bin/uconsole-activity').exists():
        subprocess.Popen([str(Path.home()/'.local/bin/uconsole-activity')], start_new_session=True)
    else:
        app.launch([], None)
else:
    print(json.dumps([{'id': key, 'name': app.get_display_name(), 'executable': app.get_executable()}
                      for key, app in apps.items()], ensure_ascii=False))
