# Шыққан видеоның аудиосын 6 с терезелермен сөз деңгейінде транскрипциялап out/NN.check.json жазады (2-өту синхроны үшін).
# Жергілікті Whisper (whisp.py), API кілт керек емес. Тіл: CREO_LANG (әдепкі kk).
import json, subprocess, sys, glob, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp
from paths import FF
n = int(sys.argv[1]); mp4 = sorted(glob.glob(f'out/{n:02d}_*.mp4'))[0]; fl = f'chunks/out{n:02d}.flac'
os.makedirs('chunks', exist_ok=True)
subprocess.run([FF, '-v', 'error', '-y', '-i', mp4, '-ac', '1', '-ar', '16000', fl], check=True)
probe = subprocess.run([FF, '-i', fl], capture_output=True, text=True).stderr
h, m, s = probe.split('Duration: ')[1].split(',')[0].split(':'); dur = int(h) * 3600 + int(m) * 60 + float(s)
lang = os.environ.get('CREO_LANG', 'kk')
ws = []
for st in [i * 6.0 for i in range(int(dur // 6) + 1)]:
    f = Path(f'chunks/o{n:02d}_{st:05.1f}.flac'); a = max(0, st - 1)
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(a), '-t', '8', '-i', fl, '-c:a', 'flac', str(f)], check=True)
    j = whisp.transcribe(str(f), 'large-v3', lang, None, True)
    ws += [{'w': w['word'], 's': round(w['start'] + a, 3), 'e': round(w['end'] + a, 3)} for w in j['words'] if st <= w['start'] + a < st + 6]
json.dump(ws, open(f'out/{n:02d}.check.json', 'w'), ensure_ascii=False); print(n, 'check words', len(ws))
