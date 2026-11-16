import os
import sys, json, glob, subprocess, importlib.util, time, requests
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from common import *
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp as t
from paths import FF as _PFF
key = t.load_api_key(); n = int(sys.argv[1])
mp4 = glob.glob(W + f'out/{n:02d}_*.mp4')[0]; fl = W + f'out/{n:02d}.check.flac'
subprocess.run([FF, '-v', 'error', '-y', '-i', mp4, '-ac', '1', '-ar', '16000', fl], check=True)
for k in range(8):
    r = t.post(None,
        data=[("model", "whisper-large-v3"), ("response_format", "verbose_json"), ("language", os.environ.get("CREO_LANG", "kk")), ("temperature", "0"), ("timestamp_granularities[]", "word")],
        files={"file": ("a.flac", open(fl, 'rb'))}, timeout=300)
    if r.status_code == 200: break
    time.sleep(15)
j = r.json(); ws = [{'w': w['word'], 's': w['start'], 'e': w['end']} for w in j['words']]
json.dump(ws, open(W + f'out/{n:02d}.check.json', 'w'), ensure_ascii=False)
print('output words:', len(ws)); print(j['text'])
