"""Жергілікті Whisper (faster-whisper, CPU) — API кілтсіз транскрипция.
Скрипттер транскрипцияны осы модуль арқылы шақырады (OpenAI-ға ұқсас жауап форматы):
  import whisp as t; key = t.load_api_key(); r = t.post(url, headers=..., data=[...], files={'file': (name, fh)})
  r.status_code == 200; r.json() -> {'text', 'words': [{'word','start','end'}], 'segments': [...]}
Модель: data ішіндегі ("model", "whisper-large-v3" | "whisper-large-v3-turbo"); CREO_WHISPER орта айнымалысы бәрін ауыстырады
(мыс. CREO_WHISPER=large-v3-turbo — жылдамырақ, бір ғана модель жүктеледі).
"""
import os, sys, tempfile

_MODELS = {}
def _model(name):
    name = os.environ.get('CREO_WHISPER') or name.replace('whisper-', '')
    if name not in _MODELS:
        from faster_whisper import WhisperModel
        print(f'[whisper] {name} жүктелуде (бірінші рет бірнеше минут)…', file=sys.stderr, flush=True)
        _MODELS[name] = WhisperModel(name, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4)
    return _MODELS[name]

def transcribe(path, model='large-v3', language=None, prompt=None, words=True):
    segs, _ = _model(model).transcribe(path, language=language, initial_prompt=prompt or None, temperature=(0.0, 0.2, 0.4, 0.6), compression_ratio_threshold=2.0,
                                       repetition_penalty=1.15, no_repeat_ngram_size=4, beam_size=5, word_timestamps=words, vad_filter=False, condition_on_previous_text=False)
    segs = list(segs)
    ws = [dict(word=w.word.strip(), start=round(w.start, 3), end=round(w.end, 3)) for s in segs for w in (s.words or [])]
    return dict(text=''.join(s.text for s in segs).strip(), words=ws,
                segments=[dict(start=s.start, end=s.end, text=s.text) for s in segs])

class _Resp:
    status_code = 200
    def __init__(self, j): self._j = j
    def json(self): return self._j

def post(url=None, headers=None, data=(), files=None, timeout=None):
    d = {}
    for k, v in data: d.setdefault(k, v)
    name, fh = files['file']
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(name)[1] or '.flac', delete=False) as tmp:
        tmp.write(fh.read()); p = tmp.name
    try:
        lang = d.get('language'); lang = None if lang in (None, 'auto') else lang
        return _Resp(transcribe(p, d.get('model', 'whisper-large-v3'), lang, d.get('prompt'), 'timestamp_granularities[]' in d))
    finally: os.unlink(p)

def load_api_key(): return None   # кілт керек емес
