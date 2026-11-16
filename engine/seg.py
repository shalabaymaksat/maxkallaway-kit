import os
import sys, subprocess, importlib.util, requests
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whisp as t
from paths import FF as _PFF
key = t.load_api_key(); FF=_PFF
a,b,model,lang=float(sys.argv[1]),float(sys.argv[2]),sys.argv[3],sys.argv[4]
prompt = sys.argv[5] if len(sys.argv)>5 else ''
f=Path('chunks/seg.flac')
subprocess.run([FF,'-v','error','-y','-ss',str(a),'-to',str(b),'-i','audio/'+(sys.argv[6] if len(sys.argv)>6 else '01')+'.flac','-c:a','flac',str(f)],check=True)
data=[("model",model),("response_format","verbose_json"),("temperature","0"),("timestamp_granularities[]","word")]
if lang!='auto': data.append(("language",lang))
if prompt: data.append(("prompt",prompt))
r=t.post(None,data=data,files={"file":(f.name,f.open('rb'))},timeout=300).json()
print(model,lang,a,b,"|",r.get("text")); print(" ".join(f"{w['word']}@{w['start']+a:.2f}" for w in r.get("words",[])))
