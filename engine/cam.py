# Камераға қараған аралықтарды табу: эталон кадрмен (адам камераға қараған сәт) 0,25 с сайын салыстырады.
#   python3 $S/cam.py REF_N REF_SEC N [N ...]     C = камера, c = күмәнді, . = экран/басқа
import subprocess, numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import FF
names = [l.strip() for l in open('list.txt')]
def frames(n):
    w, h = 18, 32
    raw = subprocess.run([FF, '-v', 'error', '-i', 'src/' + names[n - 1], '-vf', f'fps=4,scale={w}:{h},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(float)
ref = frames(int(sys.argv[1]))[int(float(sys.argv[2]) * 4)]
def score(f):
    a = f[:12].ravel() - f[:12].mean(); b = ref[:12].ravel() - ref[:12].mean()
    return (a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())
for n in map(int, sys.argv[3:]):
    s = np.array([score(f) for f in frames(n)])
    c = ''.join('C' if x > 0.6 else ('c' if x > 0.4 else '.') for x in s)
    print(n); print('\n'.join(f'{i / 4:5.1f} ' + c[i:i + 40] for i in range(0, len(c), 40)))
