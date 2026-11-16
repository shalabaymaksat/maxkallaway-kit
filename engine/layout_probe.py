#!/usr/bin/env python3
"""Кадр макетін өлшеу: экран/бет шекарасы (seam) мен бастың үсті (hair) — sub_y/hook_y таңдау үшін.
  python3 layout_probe.py 3 10 60      # NN видео, секундтар
"""
import os, sys, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FF, SRCDIR, NAMES, W
n = int(sys.argv[1])
for t in sys.argv[2:]:
    raw = subprocess.run([FF, '-v', 'error', '-ss', t, '-i', SRCDIR + NAMES[n - 1], '-frames:v', '1', '-vf', 'scale=1080:1920,format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(1920, 1080).astype(float)
    r = a[:, 100:980].mean(1); d = np.abs(np.diff(r))
    seam = sorted(int(x) for x in np.argsort(d)[-4:])
    hair = next((y for y in range(500, 1500, 10) if (a[y, 400:680] < 60).mean() > 0.4), None)
    print(f't={t}s  strong edges (seam candidates): {seam}  head top ≈ {hair}')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', t, '-i', SRCDIR + NAMES[n - 1], '-frames:v', '1', '-vf', 'scale=540:960', W + f'test/probe_{n:02d}_{t}.jpg'])
