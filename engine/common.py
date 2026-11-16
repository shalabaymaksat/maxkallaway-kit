import os, json, subprocess, numpy as np
# Жұмыс папкасы (audio/, stt/, chunks/, out/, test/, list.txt, videos.py осында) және бастапқы видеолар папкасы.
# Іске қосар алдында: export RAZBOR_WORK=<жоба>  RAZBOR_SRC="/path/to/videos"
W = os.path.join(os.path.expanduser(os.environ.get('RAZBOR_WORK', os.getcwd())), '')
SRCDIR = os.path.join(os.path.expanduser(os.environ.get('RAZBOR_SRC', W)), '')
from paths import FF
NAMES = [l.strip() for l in open(W + 'list.txt')] if os.path.exists(W + 'list.txt') else []
def pcm(n, sr=16000):
    raw = subprocess.run([FF, '-v', 'error', '-i', W + f'audio/{n:02d}.flac', '-f', 's16le', '-ac', '1', '-ar', str(sr), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
def env(n):
    p = W + f'audio/{n:02d}.env.npy'
    if os.path.exists(p): return np.load(p)
    a = pcm(n); k = len(a) // 160
    db = 20 * np.log10(np.sqrt((a[:k*160].reshape(k, 160) ** 2).mean(1) + 1e-10)).astype(np.float32)
    np.save(p, db); return db
def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            out.append([i, j]); i = j
        else: i += 1
    return out
def thr_of(db):
    lo, hi = np.percentile(db, 10), np.percentile(db, 90)
    return lo + 0.35 * (hi - lo)
def voiced(db, a=0, b=None, thr=None, mingap=0.25, minlen=0.06):
    thr = thr_of(db) if thr is None else thr
    b = len(db) / 100 if b is None else b
    e = db[int(a*100):int(b*100)]
    segs = [[a + s/100, a + t/100] for s, t in runs(e > thr)]
    m = []
    for s in segs:
        if m and s[0] - m[-1][1] < mingap: m[-1][1] = s[1]
        else: m.append(s)
    return [s for s in m if s[1] - s[0] >= minlen]
