#!/usr/bin/env python3
"""maxkallaway: hormozi-razbor render.py + Kallaway стиліндегі анимация карточкалары (тек камераға қараған бөлікте) + SFX.
Карточкалар жұмыс папкасындағы anims.py-дан (ANIMS, KEEP) оқылады.
  RAZBOR_WORK=$PWD RAZBOR_SRC=$PWD/src python3 $S/kw_render.py N [--test t ...]
Карточка сөз айтылған уақыт + 0,1 с-та «поп» болып шығады (0,16 с, блюрсыз), ауысу — таза кесу.
"""
import sys, os, wave, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R

# Эмодзи: Mac-та Apple Color Emoji шрифті (бекітілген түрі); Linux/бұлтта — Noto Emoji PNG (fonts/emoji/, жоқ болса жүктеледі)
_APPLE = '/System/Library/Fonts/Apple Color Emoji.ttc'
EMO = ImageFont.truetype(_APPLE, 160) if os.path.exists(_APPLE) and not os.environ.get('KW_NOTO') else None
from paths import FONTS as _FONTS
_EDIR = _FONTS + 'emoji/'
def _infinity(sz=512):
    # ♾️: Noto-да күлгін шаршы — Apple-дағыдай сұр ∞ белгісін өзіміз сызамыз
    im = Image.new('RGBA', (sz * 2, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    t = np.linspace(0, 2 * np.pi, 400); a = sz * 0.92
    x = a * np.cos(t) / (1 + np.sin(t) ** 2); y = a * np.sin(t) * np.cos(t) / (1 + np.sin(t) ** 2)
    pts = [(sz + float(u), sz / 2 + float(v)) for u, v in zip(x, y)]
    d.line(pts + pts[:2], fill=(110, 110, 115, 255), width=int(sz * 0.16), joint='curve')
    return im
def _noto_png(ch):
    if ch.replace('\ufe0f', '') == '\u267e': return _infinity()
    name = 'emoji_u' + '_'.join(f'{ord(c):04x}' for c in ch if ord(c) != 0xFE0F) + '.png'
    p = _EDIR + name
    if not os.path.exists(p):
        import urllib.request; os.makedirs(_EDIR, exist_ok=True)
        urllib.request.urlretrieve('https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/png/512/' + name, p)
    return Image.open(p).convert('RGBA')
INK, YEL, OR, YTR = (17, 17, 17), (255, 214, 0), (217, 119, 87), (255, 0, 0)
CARD_Y = 590          # төбе (потолок) аймағы: субтитр 335, бас үсті ~760

def f(w, s): return R.font(w, s)

def emoji(ch, size):
    if EMO is None: im = _noto_png(ch)
    else:
        im = Image.new('RGBA', (180, 180), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=EMO, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def claude_mark(size):
    s = size * 4; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    for k in range(12):
        a = k * np.pi / 6 + 0.13; r = s * (0.47 if k % 2 else 0.40)
        d.line((c, c, c + r * np.cos(a), c + r * np.sin(a)), fill=OR, width=int(s * 0.085))
    d.ellipse((c - s * .12, c - s * .12, c + s * .12, c + s * .12), fill=OR)
    return im.resize((size, size), Image.LANCZOS)

def yt_icon(h):
    w = int(h * 1.42); im = Image.new('RGBA', (w * 4, h * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), radius=h * 4 * .28, fill=YTR)
    cx, cy, r = w * 2, h * 2, h * 4 * .2
    d.polygon([(cx - r * .8, cy - r), (cx - r * .8, cy + r), (cx + r * 1.05, cy)], fill=(255, 255, 255))
    return im.resize((w, h), Image.LANCZOS)

def reel_tile(w, col):
    h = int(w * 16 / 9); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=col)
    cx, cy, r = w / 2, h / 2, w * .16
    d.polygon([(cx - r * .7, cy - r), (cx - r * .7, cy + r), (cx + r, cy)], fill=(255, 255, 255))
    return im

def card(parts, pad=(44, 30), gap=22, bg=(255, 255, 255)):
    """parts: Image немесе ('text', сөз, өлшем, highlight?) — бір қатарға тізіледі."""
    ims = []
    for p in parts:
        if isinstance(p, Image.Image): ims.append(p); continue
        _, txt, sz, hl = p
        fo = f('ExtraBold', sz); tw = int(fo.getlength(txt)); th = int(sz * 1.25)
        im = Image.new('RGBA', (tw + 24, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if hl: d.rounded_rectangle((0, int(th * .18), tw + 23, th - 2), radius=10, fill=YEL)
        d.text((12, int(th * .08)), txt, font=fo, fill=INK)
        ims.append(im)
    W_ = sum(i.width for i in ims) + gap * (len(ims) - 1) + pad[0] * 2
    H_ = max(i.height for i in ims) + pad[1] * 2
    sh = 24
    out = Image.new('RGBA', (W_ + sh * 2, H_ + sh * 2), (0, 0, 0, 0))
    m = Image.new('L', out.size, 0); ImageDraw.Draw(m).rounded_rectangle((sh, sh + 8, sh + W_, sh + H_ + 8), radius=34, fill=110)
    out.paste((0, 0, 0, 255), (0, 0), m.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(out); d.rounded_rectangle((sh, sh, sh + W_, sh + H_), radius=34, fill=bg + (255,))
    x = sh + pad[0]
    for i in ims:
        out.alpha_composite(i, (x, sh + (H_ - i.height) // 2)); x += i.width + gap
    return out

def arrow(w=70):
    im = Image.new('RGBA', (w, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((4, 30, w - 22, 30), fill=INK, width=9); d.polygon([(w - 30, 10), (w - 2, 30), (w - 30, 50)], fill=INK)
    return im

import anims
ANIMS = anims.ANIMS
N = int(sys.argv[1]); CFG = ANIMS.get(N, dict(cam=[], items=[]))
TILE_COLS = [(255, 77, 109), (124, 77, 255), (0, 184, 148)]
def build(parts):
    out = []
    for p in parts:
        if p == 'claude': out.append(claude_mark(96))
        elif p == 'yt': out.append(yt_icon(84))
        elif p == 'arrow': out.append(arrow())
        elif isinstance(p, str) and p.startswith('tiles'): out += [reel_tile(92, c) for c in TILE_COLS[:int(p[5:])]]
        elif p[0] == 'e': out.append(emoji(p[1], 96))
        else: out.append(('t', p[1], 64, p[0] == 'h'))
    return card(out)

def in_cam(src): return any(a <= src < b for a, b in CFG['cam'])
def cam_end(src): return next((b for a, b in CFG['cam'] if a <= src < b), src)

SCHED, ZOOMS = [], []
def plan(pcs, toks, brk, t, total):
    """Карточкалар мен 1,2x аралықтарын шығыс уақытпен есептейді (сөз уақыты + 0,1 с)."""
    global SCHED, ZOOMS
    items, i0, raw = CFG['items'], 0, []
    for pre, parts, sfx in items:
        # камерадағы бірінші сәйкес сөз (камерадан тыс сәйкестік өткізіледі)
        k = next((i for i in range(i0, len(toks)) if R.norm(toks[i]).startswith(R.norm(pre)) and in_cam(R.out2src(pcs, t[i] + 0.10))), None)
        if k is None: print('  !! камерадан табылмады:', pre); continue
        i0 = k + 1
        t0 = t[k] + 0.10; src = R.out2src(pcs, t0)
        raw.append((t0, R.src2out(pcs, cam_end(src)), build(parts), sfx))
    SCHED = []
    for k, (t0, ce, im, sfx) in enumerate(raw):
        nxt = raw[k + 1][0] if k + 1 < len(raw) else total
        SCHED.append((t0, min(nxt, ce, t0 + 2.4, total), im, sfx))
    # сөйлем жолдары: камерада әр 3-ші жол (1-ден бастап) таза кесумен 1,2x
    starts = [0] + [i + 1 for i, b in enumerate(brk) if b and i + 1 < len(toks)]
    ZOOMS = []
    for j, s in enumerate(starts):
        if j % 3 != 1: continue
        a = t[s]; b = t[starts[j + 1]] if j + 1 < len(starts) else total
        sa = R.out2src(pcs, a)
        if in_cam(sa): ZOOMS.append((a, min(b, R.src2out(pcs, cam_end(sa)))))
    for x in SCHED: print(f'  anim {x[0]:6.2f}-{x[1]:6.2f} {x[3]}')
    for z in ZOOMS: print(f'  zoom {z[0]:6.2f}-{z[1]:6.2f}')

_orig_cards = R.make_cards
def make_cards(toks, brk, t, total, keys):
    plan(PCS, toks, brk, t, total)
    return _orig_cards(toks, brk, t, total, keys)

def anim_frame(fr, t):
    a = next((x for x in SCHED if x[0] <= t < x[1]), None)
    if not a: return fr
    t0, _, im, _ = a
    k = (t - t0) / 0.16
    sc = 1.0 if k >= 1 else (0.6 + 0.55 * k if k < 0.8 else 1.04 - 0.04 * (k - 0.8) / 0.2)
    # тез құрастырылатын топтағы келесі карточка поп жасамай, бірден шығады
    i = SCHED.index(a)
    if i > 0 and abs(SCHED[i - 1][1] - t0) < 0.02 and t0 - SCHED[i - 1][0] < 0.6: sc = 1.0
    if sc != 1.0: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    arr = np.asarray(im).astype(np.float32)
    R.blend(fr, arr[..., :3], arr[..., 3:] / 255, 540, CARD_Y)
    return fr

DARK = {}
_orig_compose = R.compose
PCS = None
def compose(v, t, cards, cfg, hook):
    if any(a <= t < b for a, b in ZOOMS):
        im = Image.fromarray(v); w, h = int(1080 / 1.2), int(1920 / 1.2)
        v = np.asarray(im.crop(((1080 - w) // 2, (1920 - h) // 2, (1080 + w) // 2, (1920 + h) // 2)).resize((1080, 1920), Image.BICUBIC)).copy()
    # ақ экран (ноутбук беті) үстінде субтитр оқылмайды -> сол карточка қара түспен
    c = next((c for c in cards if c[0] <= t < c[1]), None)
    if c is not None:
        if c[0] not in DARK:
            reg = v[cfg['sub_y'] - 40:cfg['sub_y'] + 40, 160:920].astype(np.float32)
            DARK[c[0]] = float((reg @ [0.299, 0.587, 0.114]).mean()) > 175
        cfg = dict(cfg, dark=DARK[c[0]])
    fr = _orig_compose(v, t, cards, cfg, hook)
    return anim_frame(fr, t)

# ---------- SFX (синтез, анық естілетін деңгейде) ----------
SR = R.SR
def sfx(kind):
    n = int(SR * (0.22 if kind != 'click' else 0.12)); t = np.arange(n) / SR
    if kind in ('pop', 'pop2'):
        f0, f1 = (520, 1250) if kind == 'pop' else (700, 1600)
        ph = 2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR
        x = np.sin(ph) * np.exp(-t * 26) + 0.25 * np.sin(2 * ph) * np.exp(-t * 40)
    elif kind == 'snip':
        x = (np.random.RandomState(1).randn(n) * np.exp(-t * 60)) * 0.7
        x[int(SR * .09):] += np.random.RandomState(2).randn(n - int(SR * .09)) * np.exp(-t[:n - int(SR * .09)] * 60) * 0.7
    else:  # click
        x = np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 90) + np.random.RandomState(3).randn(n) * np.exp(-t * 200) * 0.4
    x[:int(SR * .003)] *= np.linspace(0, 1, int(SR * .003))
    return x / np.abs(x).max() * 0.55 * 32767

_orig_audio = R.build_audio
def build_audio(n, pcs, total, path):
    _orig_audio(n, pcs, total, path)
    wf = wave.open(path); a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2).astype(np.float32); wf.close()
    for t0, _, _, kind in SCHED:
        x = sfx(kind); o = int(t0 * SR)
        a[o:o + len(x)] += x[:max(0, len(a) - o), None]
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(a, -32768, 32767).astype(np.int16).tobytes())

_orig_pieces = R.pieces_for
def pieces_for(n):
    global PCS, SCHED
    pcs, total, fill = _orig_pieces(n)
    PCS = pcs
    end = R.src2out(pcs, CFG['end']) if 'end' in CFG else total
    return pcs, min(total, end), fill

_orig_wt = R.word_times
def word_times(n, cfg, pcs, total):
    """Ойнайтын видео алдындағы соңғы сөздер интерполяциямен play ішіне кетіп қалмасын: play басталар алдына қысу."""
    toks, brk, t = _orig_wt(n, cfg, pcs, total)
    for a, b in [(R.src2out(pcs, x), R.src2out(pcs, y)) for x, y in cfg.get('play', [])]:
        idx = [i for i, x in enumerate(t) if a - 0.05 <= x < b]
        for j, i in enumerate(idx):
            t[i] = max(t[i - 1] + 0.05 if i else 0, a - 0.06 - 0.15 * (len(idx) - 1 - j))
    return toks, brk, t
R.word_times = word_times

import inspect
R.KEEP = set(getattr(anims, 'KEEP', ()))   # бас әрпі сақталатын сөздер (кісі аттары т.б.)
exec(inspect.getsource(R.sub_img).replace("w.lower() if not", "w.lower() if w not in KEEP and not"), R.__dict__)
R.compose, R.build_audio, R.pieces_for, R.make_cards = compose, build_audio, pieces_for, make_cards
if __name__ == '__main__':
    R.main()
