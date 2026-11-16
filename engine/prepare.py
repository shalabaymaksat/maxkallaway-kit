#!/usr/bin/env python3
"""1-қадам: бастапқы видеолар тізімі (list.txt) + аудио (audio/NN.flac, 16 кГц моно) + бос папкалар.
  RAZBOR_WORK=<жоба> RAZBOR_SRC="/path/to/videos" python3 prepare.py
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(os.path.expanduser(os.environ.get('RAZBOR_WORK', os.getcwd())), '')
SRC = os.path.join(os.path.expanduser(os.environ.get('RAZBOR_SRC', W)), '')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import FF
for d in ['audio', 'stt', 'chunks', 'out', 'test']: os.makedirs(W + d, exist_ok=True)
vids = sorted(f for f in os.listdir(SRC) if f.lower().endswith(('.mov', '.mp4', '.m4v')) and not f.startswith('._') and '.tmp.' not in f
              and f.lower() not in ('reference.mp4',))
open(W + 'list.txt', 'w').write('\n'.join(vids) + '\n')
for i, f in enumerate(vids, 1):
    out = W + f'audio/{i:02d}.flac'
    if not os.path.exists(out):
        subprocess.run([FF, '-v', 'error', '-y', '-i', SRC + f, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'flac', out], check=True)
    print(f'{i:02d}  {f}')
if not os.path.exists(W + 'videos.py'):
    open(W + 'videos.py', 'w').write('# Әр видеоның конфигі — SKILL.md-дегі үлгіні қара\nVIDEOS = {\n}\n')
print('OK ->', W)
