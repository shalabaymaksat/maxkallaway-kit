import os
import sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
def spec_flux(n):
    a = pcm(n); hop = 160; win = 400
    k = (len(a) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(k)[:, None]
    fr = a[idx] * np.hanning(win)
    S = np.abs(np.fft.rfft(fr, 512)) ** 2
    # 24 log bands 100-4000Hz
    f = np.fft.rfftfreq(512, 1 / 16000); edges = 700 * (10 ** (np.linspace(np.log10(1 + 200 / 700), np.log10(1 + 4000 / 700), 17)) - 1)
    B = np.stack([S[:, (f >= edges[i]) & (f < edges[i+1])].mean(1) for i in range(16)], 1)
    L = np.log(B + 1e-9)
    L -= L.mean(1, keepdims=True)
    flux = np.r_[0, np.abs(np.diff(L, axis=0)).mean(1)]
    # smooth 50ms
    flux = np.convolve(flux, np.ones(5) / 5, 'same')
    return flux
def candidates(n, minlen=0.28):
    db = env(n); thr = thr_of(db); fl = spec_flux(n)
    m = min(len(db), len(fl)); db, fl = db[:m], fl[:m]
    v = db > thr
    lim = np.percentile(fl[v], 30)
    stable = v & (fl < lim)
    out = []
    for s, e in runs(stable):
        if (e - s) / 100 >= minlen: out.append((s / 100, e / 100))
    return out
if __name__ == '__main__':
    n = int(sys.argv[1])
    words = json.load(open(W + f'stt/{n:02d}.chunks.json'))
    db = env(n); thr = thr_of(db)
    for s, e in candidates(n):
        # pause before/after?
        pb = (db[max(0, int(s*100)-20):int(s*100)] < thr).mean()
        pa = (db[int(e*100):int(e*100)+20] < thr).mean()
        ctx = ' '.join(w['w'] for w in words if s - 1.0 <= w['s'] <= e + 0.6)
        print(f'{s:7.2f}-{e:7.2f} ({e-s:.2f}) pb={pb:.1f} pa={pa:.1f} | {ctx}')
