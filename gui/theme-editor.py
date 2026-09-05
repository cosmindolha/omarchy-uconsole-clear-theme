#!/usr/bin/python3
"""Small, session-local Omarchy accent editor for the uConsole."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import base64
import json
import os
import re
import shutil
import subprocess
import threading
import tomllib
import urllib.request
import urllib.error
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
THEMES = HOME / '.config/omarchy/themes'
CURRENT = HOME / '.local/state/omarchy/current'
PRESETS = {'yellow':'#FFD166', 'green':'#A9E879', 'blue':'#8FC7FF', 'white':'#F8F8F2'}
NAMES = {key: 'uconsole-clear' + ('' if key == 'yellow' else '-'+key) for key in PRESETS}
LOCK = threading.Lock()
SEQUENCES = {}

def env():
    value = os.environ.copy()
    runtime = Path('/run/user') / str(os.getuid())
    value.update(OMARCHY_PATH='/usr/share/omarchy', XDG_RUNTIME_DIR=str(runtime), LANG='en_US.UTF-8', DBUS_SESSION_BUS_ADDRESS=f'unix:path={runtime}/bus')
    value['PATH'] = '/usr/share/omarchy/bin:'+str(HOME / '.local/bin')+':'+value.get('PATH','/usr/bin')
    displays = sorted((p for p in runtime.glob('wayland-*') if not p.name.endswith('.lock')), key=lambda p:p.stat().st_mtime)
    instances = sorted((runtime/'hypr').glob('*'), key=lambda p:p.stat().st_mtime)
    if displays: value['WAYLAND_DISPLAY'] = displays[-1].name
    if instances: value['HYPRLAND_INSTANCE_SIGNATURE'] = instances[-1].name
    return value

def run(args):
    return subprocess.run(args, env=env(), check=True, capture_output=True, text=True, timeout=45).stdout.strip()

def luminance(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    rgb = [n/12.92 if n<=0.04045 else ((n+0.055)/1.055)**2.4 for n in rgb]
    return sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))

def contrast(a,b):
    a,b=sorted((luminance(a),luminance(b)))
    return (b+.05)/(a+.05)

def readable(color):
    if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color):
        raise ValueError('Use a six-digit hex color, such as #8FC7FF')
    color=color.upper()
    original=color
    # Keep accent text legible on the near-black background, including custom hues.
    channels=[int(color[i:i+2],16) for i in (1,3,5)]
    for n in range(101):
        color='#'+''.join(f'{round(c+(255-c)*n/100):02X}' for c in channels)
        if contrast(color,'#060709')>=4.5:break
    ink=max(('#060709','#F8F8F2'),key=lambda c:contrast(c,color))
    return color,ink,color!=original

def palette(color):
    accent,ink,adjusted=readable(color)
    colors=(THEMES/'uconsole-clear/colors.toml').read_text().replace('#FFD166',accent)
    shell=(THEMES/'uconsole-clear/shell.toml').read_text().replace('#FFD166',accent)
    shell=shell.replace('selected-text = "#060709"',f'selected-text = "{ink}"')
    return accent,ink,adjusted,colors,shell

def make_preview(target,accent,ink):
    """Omarchy's theme picker prefers preview.png over the actual wallpaper."""
    label=next((key.title() for key,value in PRESETS.items() if value==accent),'Custom')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
      <rect width="1280" height="720" fill="#060709"/>
      <g transform="translate(154 86) scale(.76)" font-family="JetBrains Mono, monospace" fill="#F8F8F2">
        <rect width="1280" height="60" fill="#020304"/>
        <path d="M0 60H1280" stroke="#53616B"/>
        <g font-size="27"><text x="25" y="39">Menu</text><text x="130" y="39" fill="{accent}">[1]</text><text x="205" y="39">2  3  4  5</text><text x="835" y="39">11:44   Wi-Fi  Bat</text></g>
        <rect x="24" y="90" width="748" height="510" rx="8" fill="#060709" stroke="{accent}" stroke-width="3"/>
        <rect x="26" y="92" width="744" height="51" rx="6" fill="#151A1F"/>
        <text x="47" y="127" font-size="25">Terminal</text>
        <g font-size="31"><text x="54" y="201" fill="{accent}">~/projects $</text><text x="305" y="201">ready</text>
          <text x="54" y="263">Readable text.</text><text x="54" y="312">Near-black background.</text>
          <text x="54" y="401" fill="{accent}">Clear / {escape(label)}</text><text x="54" y="450" fill="#C0C8CE">{accent} accent</text></g>
        <rect x="54" y="503" width="45" height="34" fill="{accent}"/><rect x="111" y="503" width="45" height="34" fill="#F8F8F2"/><rect x="168" y="503" width="45" height="34" fill="#C0C8CE"/><rect x="225" y="503" width="45" height="34" fill="#53616B"/>
        <rect x="798" y="90" width="458" height="510" rx="8" fill="#101419" stroke="#53616B" stroke-width="2"/>
        <text x="826" y="137" font-size="25" fill="#C0C8CE">Commands</text>
        <rect x="817" y="169" width="420" height="64" rx="6" fill="{accent}"/>
        <g font-size="31"><text x="841" y="212" fill="{ink}">Theme colors</text><text x="841" y="291">Keybindings</text><text x="841" y="370">Terminal</text><text x="841" y="449">Files</text></g>
        <text x="28" y="667" font-size="30" fill="{accent}">Clear / {escape(label)}</text><text x="794" y="667" font-size="26" fill="#C0C8CE">Large text · High contrast</text>
      </g></svg>'''
    temporary=target/'preview.png.new'
    subprocess.run(['rsvg-convert','--output',str(temporary)],input=svg,text=True,check=True,capture_output=True,timeout=15)
    temporary.replace(target/'preview.png')
    # The stock picker caches directory mtimes at one-second resolution.
    (HOME/'.cache/omarchy/theme-selector/fast-signature').unlink(missing_ok=True)

def make_variant(name,color):
    accent,ink,adjusted,colors,shell=palette(color)
    target=THEMES/name
    if name!='uconsole-clear':
        shutil.copytree(THEMES/'uconsole-clear',target,dirs_exist_ok=True)
    for filename,text in [('colors.toml',colors),('shell.toml',shell)]:
        temporary=target/(filename+'.new')
        temporary.write_text(text)
        temporary.replace(target/filename)
    make_preview(target,accent,ink)
    return accent,ink,adjusted

def state():
    colors=tomllib.loads((CURRENT/'theme/colors.toml').read_text())
    name=(CURRENT/'theme.name').read_text().strip()
    accent=colors['accent']
    return {'accent':accent,'ink':readable(accent)[1],'theme':name,'presets':PRESETS}

def preview(colors,shell,accent):
    run(['omarchy-shell','shell','applyTheme',base64.b64encode(colors.encode()).decode(),base64.b64encode(shell.encode()).decode()])
    run(['hyprctl','-i','0','eval','hl.config({ general = { col = { active_border = "rgb('+accent[1:]+')" } } })'])

def dictation_request(data=None):
    headers = {}
    if data is not None:
        headers = {'Content-Type': 'application/json', 'X-Uconsole-Settings':
            (HOME/'.config/uconsole/dictation-settings.token').read_text().strip()}
    request = urllib.request.Request('http://127.0.0.1:8769/' + ('settings' if data is not None else 'health'),
        data=json.dumps(data).encode() if data is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError(json.loads(error.read()).get('detail', 'Settings request failed')) from error

def dictation_state():
    return dictation_request()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass
    def respond(self,status,data,kind='application/json'):
        body=json.dumps(data).encode() if kind=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=self.path.split('?')[0]
        try:
            if path=='/api/dictation':return self.respond(200,dictation_state())
            if path=='/api/state':return self.respond(200,state())
            files={'/':'theme-editor.html','/keys':'keyboard.html','/dictation':'dictation.html'}
            if path in files:return self.respond(200,(ROOT/files[path]).read_bytes(),'text/html; charset=utf-8')
            self.respond(404,{'error':'Not found'})
        except Exception as e:self.respond(500,{'error':str(e)})
    def do_POST(self):
        # Only this local UI can mutate a theme. No CORS or external origins.
        if self.headers.get('Origin')!='http://'+self.headers.get('Host','') or self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self.respond(403,{'error':'Local editor requests only'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=2048:raise ValueError('Invalid request size')
            data=json.loads(self.rfile.read(length))
            if self.path=='/api/dictation':
                return self.respond(200,dictation_request(data))
            client=str(data.get('client',''))[:80];seq=int(data.get('seq',0))
            with LOCK:
                if seq<=SEQUENCES.get(client,-1):return self.respond(200,{'stale':True})
                SEQUENCES[client]=seq
                if self.path=='/api/revert':
                    current=state()
                    preview((CURRENT/'theme/colors.toml').read_text(),(CURRENT/'theme/shell.toml').read_text(),current['accent'])
                    return self.respond(200,current)
                if self.path not in ('/api/preview','/api/apply'):return self.respond(404,{'error':'Not found'})
                accent,ink,adjusted,colors,shell=palette(data.get('accent'))
                if self.path=='/api/preview':preview(colors,shell,accent)
                else:
                    choice=next((k for k,v in PRESETS.items() if v==accent),'custom')
                    name=NAMES.get(choice,'uconsole-clear-custom')
                    make_variant(name,accent)
                    run(['omarchy-theme-set',name])
                return self.respond(200,dict(state(),accent=accent,ink=ink,adjusted=adjusted))
        except (ValueError,KeyError,json.JSONDecodeError) as e:self.respond(400,{'error':str(e)})
        except Exception as e:self.respond(500,{'error':str(e)})

if __name__=='__main__':
    for choice,color in PRESETS.items():
        make_variant(NAMES[choice],color)
    custom=THEMES/'uconsole-clear-custom'
    if (custom/'colors.toml').is_file():
        color=tomllib.loads((custom/'colors.toml').read_text())['accent']
        make_preview(custom,color,readable(color)[1])
    ThreadingHTTPServer(('127.0.0.1',8768),Handler).serve_forever()
