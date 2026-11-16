import os
import sys, json, subprocess, importlib.util, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp as t
from paths import FF as _PFF
key = t.load_api_key()
PROMPT = os.environ.get("RAZBOR_PROMPT", "Claude, Instagram, рилс, таргет, клиент, курс.")
os.makedirs(W + 'chunks', exist_ok=True)
def cuts_for(n):
    db = env(n); dur = len(db) / 100
    sil = [(s/100, e/100) for s, e in runs(db < thr_of(db)) if e - s >= 15]
    cuts = [0.0]
    while dur - cuts[-1] > 30:
        cand = [s for s in sil if cuts[-1] + 12 < (s[0]+s[1])/2 < cuts[-1] + 28]
        c = max(cand, key=lambda s: s[1]-s[0]) if cand else (cuts[-1]+25, cuts[-1]+25)
        cuts.append(round((c[0]+c[1])/2, 2))
    cuts.append(dur); return cuts
def job(arg):
    n, i, a, b = arg
    f = Path(W) / 'chunks' / f'{n:02d}_{i:02d}.flac'
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(a), '-to', str(b), '-i', W + f'audio/{n:02d}.flac', '-c:a', 'flac', str(f)], check=True)
    data = [("model", "whisper-large-v3"), ("response_format", "verbose_json"), ("language", os.environ.get("CREO_LANG", "kk")), ("temperature", "0"), ("prompt", PROMPT),
            ("timestamp_granularities[]", "word"), ("timestamp_granularities[]", "segment")]
    for k in range(10):
        with f.open('rb') as fh:
            r = t.post(None, data=data, files={"file": (f.name, fh)}, timeout=300)
        if r.status_code == 200: break
        time.sleep(20)
    j = r.json()
    return n, i, a, b, [{'w': w['word'], 's': round(w['start']+a, 3), 'e': round(w['end']+a, 3)} for w in j.get('words', [])], j.get('text', '')
jobs = []
ONLY = [int(x) for x in sys.argv[1:]]
for n in (ONLY or range(1, len(NAMES) + 1)):
    c = cuts_for(n); jobs += [(n, i, c[i], c[i+1]) for i in range(len(c)-1)]
res = {}
with ThreadPoolExecutor(1) as ex:
    for n, i, a, b, w, txt in ex.map(job, jobs):
        res.setdefault(n, []).append((i, a, b, w, txt))
for n, lst in res.items():
    lst.sort()
    json.dump([x for l in lst for x in l[3]], open(W + f'stt/{n:02d}.chunks.json', 'w'), ensure_ascii=False)
    json.dump([[l[1], l[2], l[4]] for l in lst], open(W + f'stt/{n:02d}.chunktext.json', 'w'), ensure_ascii=False)
    print(n, len(lst), 'chunks', sum(len(l[3]) for l in lst), 'words', flush=True)
