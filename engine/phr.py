"""Кідірістер бойынша фразаларға бөліп, әрқайсысын бөлек транскрипциялау — қайта бастаған жерлерді табу үшін."""
import sys, subprocess, importlib.util, requests, json, time, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.environ.get('RAZBOR_WORK', '.'))
import render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp as t
from paths import FF as _PFF
key = t.load_api_key(); FF = _PFF
n = int(sys.argv[1]); gap = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
lang = os.environ.get('CREO_LANG', 'kk')   # орысша видео: CREO_LANG=ru
db = R.env(n); thr = R.thr_of(db); dur = len(db) / 100
vs = R.voiced(db, 0, dur, thr=thr, mingap=gap)
out = []
for i, (s, e) in enumerate(vs):
    if e - s < 0.3: continue
    f = Path(f'chunks/p{n:02d}_{i:03d}.flac')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', f'{max(0,s-0.05):.2f}', '-t', f'{e-s+0.15:.2f}', '-i', f'audio/{n:02d}.flac', '-c:a', 'flac', str(f)], check=True)
    for k in range(8):
        r = t.post(None,
            data=[("model", "whisper-large-v3"), ("response_format", "json"), ("language", lang), ("temperature", "0")], files={"file": (f.name, f.open('rb'))}, timeout=120)
        if r.status_code == 200: tx = r.json().get('text', '').strip(); break
        time.sleep(12)
    else: tx = 'ERR'
    out.append((round(s, 2), round(e, 2), tx)); print(f'{s:6.2f}-{e:6.2f} | {tx}', flush=True)
json.dump(out, open(f'stt/{n:02d}.phr.json', 'w'), ensure_ascii=False)
