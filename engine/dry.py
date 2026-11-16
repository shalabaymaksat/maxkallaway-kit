# Субтитр карточкаларының ешқайсысы жоғалмағанын рендерсіз тексереді: python3 $S/dry.py N
import sys, io, contextlib
n=int(sys.argv[1]); sys.argv=['x',str(n)]
with contextlib.redirect_stdout(io.StringIO()):
    import kw_render as K  # hormozi render.py-ды өзі жүктейді
    R = K.R
    cfg=R.VIDEOS[n]; R.FPS_STR,R.FPS=R.src_fps(n)
    pcs,total,_=R.pieces_for(n); toks,brk,t=R.word_times(n,cfg,pcs,total)
    cards=R.make_cards(toks,brk,t,total,cfg.get('keys',[]))
po=[(R.src2out(pcs,a),R.src2out(pcs,b)) for a,b in cfg.get('play',[])]
kept=[c for c in cards if not any(a-0.05<=c[0]<b for a,b in po)]
shown=' '.join(w for c in kept for w,_ in c[2]).split()
print(n,'tokens',len(toks),'shown',len(shown))
if len(shown)<len(toks):
    lost=[c for c in cards if c not in kept]
    for c in lost: print('  LOST', round(c[0],2), ' '.join(w for w,_ in c[2]))
