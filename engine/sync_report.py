#!/usr/bin/env python3
"""Субтитр синхронын тексеру: out/NN.cards.txt карточкаларын out/NN.check.json (шыққан аудио транскрипциясы) сөздерімен салыстырады.
  python3 sync_report.py 3     -> matched X/Y, median diff (≈0.02 с болуы керек)
"""
import os, sys, json, re, difflib, statistics
W = os.path.join(os.path.expanduser(os.environ.get('RAZBOR_WORK', os.getcwd())), '')
n = int(sys.argv[1])
norm = lambda s: re.sub(r'[^a-zа-яәіңғүұқөһё0-9]', '', s.lower())[:4]
ws = json.load(open(W + f'out/{n:02d}.check.json'))
cards = [(float(m.group(1)), m.group(3).replace('*', '')) for m in (re.match(r'\s*([\d.]+)-\s*([\d.]+) (.*)', l) for l in open(W + f'out/{n:02d}.cards.txt')) if m]
sm = difflib.SequenceMatcher(None, [norm(c[1].split()[0]) for c in cards], [norm(w['w']) for w in ws], autojunk=False)
d = [cards[b.a + k][0] - ws[b.b + k]['s'] for b in sm.get_matching_blocks() for k in range(b.size)]
print('matched', len(d), '/', len(cards), 'median', round(statistics.median(d), 3), '|d|>0.4:', sum(abs(x) > 0.4 for x in d))
