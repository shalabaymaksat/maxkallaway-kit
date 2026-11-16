#!/usr/bin/env python3
"""Сентябрь видеолары: кідіріс/ыңылдау қию + референс стиліндегі хук және субтитр.
  python3 render.py 1                 # толық рендер -> out/NN_name.mp4
  python3 render.py 1 --test 1.0 20   # тек кадрлар (test/)
"""
import sys, os, re, json, wave, difflib, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser(os.environ.get('RAZBOR_WORK', os.getcwd())))  # videos.py жұмыс папкасында
from common import W as WD, FF, SRCDIR, NAMES, env, thr_of, voiced, runs
from videos import VIDEOS

W, H = 1080, 1920
FPS_STR, FPS = '24000/1001', 24000 / 1001  # main() бастапқы видеоның r_frame_rate-іне ауыстырады (қате fps = ерін мен дыбыс сәйкессіздігі)
def src_fps(n):
    fp = FF.replace('ffmpeg', 'ffprobe') if FF != 'ffmpeg' else 'ffprobe'
    r = subprocess.run([fp, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0',
                        SRCDIR + NAMES[n - 1]], capture_output=True, text=True).stdout.strip()
    r = (r.split() or ['24000/1001'])[0].strip(',')
    a, b = r.split('/')
    fps = int(a) / int(b)
    if fps > 31: r, fps = '30/1', 30.0   # 60/120 fps -> 30
    return r, fps
SR = 48000
from paths import FONTS as MF
_fc = {}
def font(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(MF + f'Montserrat-{w}.ttf', s)
    return _fc[k]
RED = (227, 6, 19)
WHITE = (255, 255, 255)
HOOK_T = 3.8
# Видео толық экранда қалады. Мәтіннің қауіпсіз аймағы (Frame 458 нұсқаулығы): x 96–984, y 232–1393,
# оң жақ төменгі ойық: x>907 және y>1112 — ол жерге мәтін қоймау.
VW, VH = 1080, 1920

def norm(s): return re.sub(r'[^a-zа-яәіңғүұқөһё0-9]', '', s.lower())

# ---------- кесінділер ----------
def is_filler(txt):
    t = norm(txt)
    return len(t) <= 6 and set(t) <= set('ыэәеөаимуүоө')

def pieces_for(n):
    db = env(n); thr = thr_of(db); dur = len(db) / 100
    fill = list(VIDEOS.get(n, {}).get('cut', []))
    p = WD + f'stt/{n:02d}.cands.json'
    if os.path.exists(p):
        fill += [(c['s'], c['e']) for c in json.load(open(p)) if is_filler(c['txt'])]
    vs = voiced(db, 0, dur, thr=thr, mingap=0.25)
    # ыңылдауларды алып тастау
    segs = []
    for s, e in vs:
        cur = [[s, e]]
        for fs, fe in fill:
            nxt = []
            for a, b in cur:
                if fe <= a or fs >= b: nxt.append([a, b]); continue
                if fs - a > 0.05: nxt.append([a, fs])
                if b - fe > 0.05: nxt.append([fe, b])
            cur = nxt
        segs += cur
    out, pcs = 0.0, []
    for s, e in segs:
        s, e = max(0, s - 0.07), min(dur, e + 0.10)
        if pcs and s <= pcs[-1][1] + 0.02:
            out += e - pcs[-1][1]; pcs[-1][1] = e; continue
        pcs.append([s, e, out]); out += e - s
    return pcs, out, fill

def src2out(pcs, t):
    for s, e, o in pcs:
        if t < s: return o
        if t <= e: return o + t - s
    return pcs[-1][2] + pcs[-1][1] - pcs[-1][0]

def out2src(pcs, t):
    for s, e, o in pcs:
        if o <= t < o + e - s: return s + t - o
    return pcs[-1][1]

# ---------- сөз тайминг ----------
def snap(db, thr, t):
    i = int(t * 100)
    if 3 <= i < len(db) and db[i] > thr and db[i - 3:i].min() > thr: return t + 0.02
    for k in range(i, min(len(db), i + 40)):
        if db[k] > thr: return k / 100 + 0.04
    return t

def align(toks, ws, times_fallback=None):
    sm = difflib.SequenceMatcher(None, [norm(t)[:4] for t in toks], [norm(w['w'])[:4] for w in ws], autojunk=False)
    anc = {}
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            i = b.a + k
            if b.size < 2 and len(norm(toks[i])) < 5: continue
            anc[i] = ws[b.b + k]['s']
    good, last = [], -1
    for i in sorted(anc):
        if anc[i] > last: good.append(i); last = anc[i]
    return {i: anc[i] for i in good}

def word_times(n, cfg, pcs, total):
    db = env(n); thr = thr_of(db)
    lines = [l.split() for l in cfg['text'].strip().split('\n')]
    toks, brk, manual = [], [], {}
    for l in lines:
        if l and l[0].startswith('@'): manual[len(toks)] = float(l[0][1:]); l = l[1:]
        for j, t in enumerate(l): toks.append(t); brk.append(j == len(l) - 1)
    ws = json.load(open(WD + f'stt/{n:02d}.chunks.json'))
    play = cfg.get('play', [])
    ws = [w for w in ws if src2out(pcs, w['s']) < total and not any(a <= w['s'] < b for a, b in play)]
    anc = align(toks, ws)
    # src -> out уақыт
    t = [None] * len(toks)
    for i, s in anc.items(): t[i] = src2out(pcs, snap(db, thr, s))
    for i, s in manual.items(): t[i] = src2out(pcs, snap(db, thr, s))
    # 2-өту: шығыс аудио транскрипциясы
    p2 = WD + f'out/{n:02d}.check.json'
    if os.path.exists(p2) and cfg.get('pass2', True):
        w2 = json.load(open(p2))
        po = [(src2out(pcs, a), src2out(pcs, b)) for a, b in cfg.get('play', [])]
        w2 = [w for w in w2 if not any(a <= w['s'] < b for a, b in po)]
        a2 = align(toks, w2)
        for i, s in a2.items():
            if i in manual: continue
            if t[i] is None or abs(t[i] - s) < 2.5:
                t[i] = src2out(pcs, snap(db, thr, out2src(pcs, s)))
    # интерполяция (әріп саны бойынша)
    lens = np.array([len(x) + 1 for x in toks], float); cum = np.concatenate([[0], np.cumsum(lens)])
    idx = [i for i in range(len(toks)) if t[i] is not None]
    # монотондылық
    clean, last = [], -1
    for i in idx:
        if t[i] > last: clean.append(i); last = t[i]
    for i in idx:
        if i not in clean: t[i] = None
    pts = [(-1, 0.0, 0.0)] + [(i, cum[i], t[i]) for i in clean] + [(len(toks), cum[-1], total)]
    for (i0, c0, t0), (i1, c1, t1) in zip(pts, pts[1:]):
        for k in range(i0 + 1, i1):
            t[k] = t0 + (t1 - t0) * (cum[k] - c0) / max(1e-6, c1 - c0)
    for i in range(1, len(t)):
        if t[i] < t[i - 1] + 0.1: t[i] = t[i - 1] + 0.1
    return toks, brk, t

def make_cards(toks, brk, t, total, keys):
    cards, cur = [], []
    for i, w in enumerate(toks):
        cur.append(i)
        txt = ' '.join(toks[j] for j in cur)
        nxt_len = len(txt) + 1 + (len(toks[i + 1]) if i + 1 < len(toks) else 0)
        gap = (t[i + 1] - t[i]) if i + 1 < len(toks) else 9
        if brk[i] or len(cur) >= 3 or nxt_len > 19 or gap > 0.9:
            cards.append(cur); cur = []
    if cur: cards.append(cur)
    keyn = [norm(k) for k in keys]
    res = []
    for k, c in enumerate(cards):
        st = t[c[0]]
        en = t[cards[k + 1][0]] if k + 1 < len(cards) else total
        en = min(en, t[c[-1]] + 1.0)
        hit = [j for j in c if any(norm(toks[j]).startswith(kk) for kk in keyn if kk)]
        prev = res[-1][3] if res else set()
        hit = [j for j in hit if norm(toks[j])[:5] not in prev]
        b = max(hit, key=lambda j: len(toks[j])) if hit else None
        words = [(toks[j], j == b) for j in c]
        res.append((st, en, words, {norm(toks[b])[:5]} if b is not None else set()))
    return res

# ---------- графика ----------
_cache = {}
def sub_img(words, dark=False):
    key = (tuple(words), dark)
    if key in _cache: return _cache[key]
    size = 56
    fr, fb = font('SemiBold', size), font('ExtraBold', size)
    sp = fr.getlength(' ')
    parts = [(w.lower() if not re.search(r'[A-Z]|[А-ЯӘІҢҒҮҰҚӨҺ]{2}', w) else w, b) for w, b in words]
    widths = [(fb if b else fr).getlength(w) for w, b in parts]
    tw = sum(widths) + sp * (len(parts) - 1)
    pad = 30
    im = Image.new('RGBA', (int(tw + pad * 2), size + pad * 2 + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for (w, b), ww in zip(parts, widths):
        d.text((x, pad), w, font=fb if b else fr, fill=((17, 17, 17) if dark else WHITE) + (255,))
        x += ww + sp
    a = im.getchannel('A')
    sh = Image.new('RGBA', im.size, (255, 255, 255, 0) if dark else (0, 0, 0, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, int(v * 1.6))))
    sh2 = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh2.alpha_composite(sh, (0, 3))
    out = Image.alpha_composite(sh2, im)
    arr = np.asarray(out).astype(np.float32)
    _cache[key] = (arr[..., :3], arr[..., 3:] / 255)
    return _cache[key]

def wrap(txt, f, maxw):
    lines, cur = [], ''
    for w in txt.split():
        c = (cur + ' ' + w).strip()
        if f.getlength(c) > maxw and cur: lines.append(cur); cur = w
        else: cur = c
    return lines + [cur]

def hook_img(txt):
    maxw = 700
    choice = None
    for size in range(64, 42, -2):
        f = font('ExtraBold', size); lines = wrap(txt, f, maxw)
        if len(lines) <= 2 and max(f.getlength(l) for l in lines) <= maxw: choice = (size, f, lines); break
    for nl in (3, 4):
        if choice is not None and choice[0] >= 52: break
        for size in range(64, 40, -2):
            f = font('ExtraBold', size); lines = wrap(txt, f, maxw)
            if len(lines) <= nl and max(f.getlength(l) for l in lines) <= maxw: choice = (size, f, lines); break
        if choice is not None and choice[0] >= 50: break
    size, f, lines = choice
    lh = int(size * 1.18)
    tw = max(f.getlength(l) for l in lines)
    padx, pady = 34, 22
    bw, bh = int(tw + padx * 2), int(lh * len(lines) + pady * 2 - (lh - size) + 6)
    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=18, fill=RED + (255,))
    for i, l in enumerate(lines):
        d.text((bw / 2, pady + i * lh), l, font=f, fill=WHITE, anchor='ma')
    arr = np.asarray(im).astype(np.float32)
    return arr[..., :3], arr[..., 3:] / 255

def blend(frame, rgb, a, cx, cy):
    h, w = a.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    sub = frame[ys0:ys1, xs0:xs1].astype(np.float32)
    rr, aa = rgb[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0], a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    frame[ys0:ys1, xs0:xs1] = (sub * (1 - aa) + rr * aa).astype(np.uint8)

# ---------- аудио/видео ----------
def build_audio(n, pcs, total, path):
    src = WD + f'audio/{n:02d}_48k.wav'
    if not os.path.exists(src):
        subprocess.run([FF, '-v', 'error', '-y', '-i', SRCDIR + NAMES[n - 1], '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', src], check=True)
    wf = wave.open(src)
    out = np.zeros((int(total * SR) + SR, 2), np.float32)
    for s, e, o in pcs:
        a0, k = int(round(s * SR)), int(round((e - s) * SR))
        wf.setpos(a0); x = np.frombuffer(wf.readframes(k), np.int16).reshape(-1, 2).astype(np.float32)
        f = min(int(0.012 * SR), len(x) // 2); r = np.linspace(0, 1, f)[:, None]
        x[:f] *= r; x[len(x) - f:] *= r[::-1]
        o0 = int(round(o * SR)); out[o0:o0 + len(x)] += x
    out = out[:int(total * SR)]
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(out, -32768, 32767).astype(np.int16).tobytes())

class Reader:
    def __init__(self, n, t0=0.0):
        self.t0 = t0
        self.p = subprocess.Popen([FF, '-v', 'error', '-hwaccel', 'videotoolbox', '-ss', f'{t0:.3f}', '-i', SRCDIR + NAMES[n - 1],
                                   '-vf', f'fps={FPS_STR},scale={VW}:{VH}:flags=bicubic', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.k, self.cur = -1, None
    def get(self, ts):
        fs = VW * VH * 3
        while self.cur is None or self.t0 + (self.k + 0.5) / FPS < ts:
            b = self.p.stdout.read(fs)
            if len(b) < fs: break
            self.cur = np.frombuffer(b, np.uint8).reshape(VH, VW, 3); self.k += 1
        return self.cur.copy()
    def close(self): self.p.stdout.close(); self.p.kill()

def compose(v, t, cards, cfg, hook):
    fr = v.copy()
    sy = cfg['sub_y']
    if t < HOOK_T:
        hy = cfg['hook_y']
        if sy > hy: hy = min(hy, sy - 82 - hook[1].shape[0] / 2)
        blend(fr, *hook, cfg.get('hook_x', W / 2), hy)
    c = next((c for c in cards if c[0] <= t < c[1]), None)
    if c: blend(fr, *sub_img(tuple(c[2]), cfg.get('dark', False)), W / 2, sy)
    return fr

def main():
    global FPS_STR, FPS
    n = int(sys.argv[1]); cfg = VIDEOS[n]
    FPS_STR, FPS = src_fps(n)
    pcs, total, fill = pieces_for(n)
    toks, brk, t = word_times(n, cfg, pcs, total)
    cards = make_cards(toks, brk, t, total, cfg.get('keys', []))
    po = [(src2out(pcs, a), src2out(pcs, b)) for a, b in cfg.get('play', [])]
    cards = [c for c in cards if not any(a - 0.05 <= c[0] < b for a, b in po)]
    cards = [(st, min(en, next((a for a, b in po if a > st), en)), w, k) for st, en, w, k in cards]
    hook = hook_img(cfg['hook'])
    os.makedirs(WD + 'out', exist_ok=True); os.makedirs(WD + 'test', exist_ok=True)
    src_dur = len(env(n)) / 100
    print(f'video {n} @{FPS_STR}fps: {src_dur:.1f}s -> {total:.1f}s ({len(pcs)} pieces, {len(fill)} fillers cut), {len(cards)} cards', flush=True)
    with open(WD + f'out/{n:02d}.cards.txt', 'w') as fh:
        for st, en, ws, _ in cards: fh.write(f'{st:7.2f}-{en:7.2f} ' + ' '.join(('*' + w + '*') if b else w for w, b in ws) + '\n')
    if '--test' in sys.argv:
        for x in sys.argv[sys.argv.index('--test') + 1:]:
            tt = float(x); r = Reader(n, max(0, out2src(pcs, tt) - 0.05)); fr = r.get(out2src(pcs, tt)); r.close()
            Image.fromarray(compose(fr, tt, cards, cfg, hook)).resize((540, 960)).save(WD + f'test/{n:02d}_{tt:06.2f}.jpg', quality=88)
        return
    wav = WD + f'out/{n:02d}.wav'; build_audio(n, pcs, total, wav)
    out = WD + f'out/{n:02d}_{os.path.splitext(NAMES[n - 1])[0]}.mp4'
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', FPS_STR, '-i', '-', '-i', wav,
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    r = Reader(n)
    for fi in range(int(total * FPS)):
        tt = fi / FPS
        fr = r.get(out2src(pcs, tt))
        enc.stdin.write(compose(fr, tt, cards, cfg, hook).tobytes())
        if fi % 480 == 0: print(f'  {tt:5.1f}/{total:.1f}', flush=True)
    r.close(); enc.stdin.close(); enc.wait()
    print('OK', out)

if __name__ == '__main__':
    main()
