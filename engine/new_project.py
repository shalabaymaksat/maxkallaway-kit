#!/usr/bin/env python3
"""Жаңа жоба: python3 engine/new_project.py <аты> [видео файлдар немесе URL ...]
 - файлдар inbox/-тан алынады (немесе берілген жол), URL болса жүктеледі (Google Drive/Dropbox/тікелей сілтеме)
 - projects/<аты>/src/ ішіне сілтеме, list.txt, audio/, videos.py/broll2.py/cuts.py үлгілері
"""
import os, sys, re, subprocess, shutil
E = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(E)
sys.path.insert(0, E); from paths import HOME
HOME = HOME.rstrip('/')
name, items = sys.argv[1], sys.argv[2:]
P = os.path.join(HOME, 'projects', name); os.makedirs(P + '/src', exist_ok=True); os.makedirs(os.path.join(HOME, 'inbox'), exist_ok=True)
def fetch_folder(url):
    """Google Drive папкасы («Anyone with the link»): ішіндегі барлық видеоны inbox/<папка>/-ға жүктейді (gdown, ≤50 файл)."""
    import gdown
    fid = re.search(r'folders/([\w-]+)', url).group(1); out = os.path.join(HOME, 'inbox', fid)
    gdown.download_folder(url, output=out, quiet=True, remaining_ok=True)
    vids = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(out) for f in fs if f.lower().endswith(('.mov', '.mp4', '.m4v')))
    print('папкадан жүктелді:', len(vids), 'видео'); return vids
def fetch(url):
    import requests
    m = re.search(r'drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([\w-]+)', url)
    if m: url = f'https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t'
    if 'dropbox.com' in url: url = re.sub(r'dl=0', 'dl=1', url) + ('' if 'dl=' in url else ('&' if '?' in url else '?') + 'dl=1')
    r = requests.get(url, stream=True, timeout=600, allow_redirects=True); r.raise_for_status()
    cd = r.headers.get('content-disposition', ''); m = re.search(r'filename="?([^";]+)', cd)
    fn = m.group(1) if m else (url.split('?')[0].rstrip('/').split('/')[-1] or 'video.mp4')
    if not fn.lower().endswith(('.mov', '.mp4', '.m4v')): fn += '.mp4'
    out = os.path.join(HOME, 'inbox', fn)
    with open(out, 'wb') as f:
        for ch in r.iter_content(1 << 20): f.write(ch)
    print('жүктелді:', fn, os.path.getsize(out) // (1 << 20), 'MB'); return out
if not items: items = [os.path.join(HOME, 'inbox', f) for f in sorted(os.listdir(os.path.join(HOME, 'inbox'))) if f.lower().endswith(('.mov', '.mp4', '.m4v'))]
srcs = []
for it in items:
    if 'drive.google.com/drive/folders/' in it: srcs += fetch_folder(it)
    else: srcs.append(fetch(it) if it.startswith('http') else (it if os.path.exists(it) else os.path.join(HOME, 'inbox', it)))
for src in srcs:
    dst = os.path.join(P, 'src', os.path.basename(src))
    if not os.path.exists(dst): os.symlink(os.path.abspath(src), dst)
for t in sorted(os.listdir(os.path.join(ROOT, 'templates'))):
    if not os.path.exists(os.path.join(P, t)): shutil.copy(os.path.join(ROOT, 'templates', t), P)
env = dict(os.environ, RAZBOR_WORK=P + '/', RAZBOR_SRC=P + '/src/')
subprocess.run([sys.executable, os.path.join(E, 'prepare.py')], env=env, check=True)
print('жоба:', P)
