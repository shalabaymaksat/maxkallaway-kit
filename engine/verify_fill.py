import os
import sys, json, subprocess, importlib.util, time, requests
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from fillers import candidates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp as t
from paths import FF as _PFF
key = t.load_api_key()
n = int(sys.argv[1]); minlen = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
out = []
for s, e in candidates(n, minlen):
    f = Path(W) / 'chunks' / f'cand_{n:02d}_{s:.2f}.wav'
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(max(0, s - 0.03)), '-to', str(e + 0.03), '-i', W + f'audio/{n:02d}.flac', '-af', 'apad=pad_dur=0.6', str(f)], check=True)
    for k in range(8):
        r = t.post(None,
                          data=[("model", "whisper-large-v3"), ("response_format", "json"), ("language", os.environ.get("CREO_LANG", "kk")), ("temperature", "0"), ("prompt", "ыы, эээ, ммм")],
                          files={"file": (f.name, f.open('rb'))}, timeout=120)
        if r.status_code == 200: break
        time.sleep(10)
    txt = r.json().get('text', '').strip()
    out.append(dict(s=s, e=e, txt=txt))
    print(f'{s:7.2f}-{e:7.2f} ({e-s:.2f}) -> "{txt}"', flush=True)
json.dump(out, open(W + f'stt/{n:02d}.cands.json', 'w'), ensure_ascii=False)
