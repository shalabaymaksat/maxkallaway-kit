#!/bin/bash
# Толық рендер: 1-өту → шыққан аудионы қайта тану (mkcheck, жергілікті Whisper) → 2-өту → ready/<папка>/
#   cd <жоба>; bash $E/run.sh 1 2 3
S="$(cd "$(dirname "$0")" && pwd)"; ROOT=$(dirname "$S")
export RAZBOR_WORK=$PWD/ RAZBOR_SRC=$PWD/src/
DST=${KW_DST:-${CREO_HOME:-$ROOT}/ready/$(basename "$PWD")}
mkdir -p out chunks "$DST"
for n in "$@"; do
  nn=$(printf %02d $n)
  rm -f out/$nn.check.json
  python3 -W ignore "$S/kw_render.py" $n > out/$nn.log1 2>&1 || { echo "FAIL1 $n"; continue; }
  python3 -W ignore "$S/mkcheck.py" $n > out/$nn.logc 2>&1 || { echo "FAILc $n"; continue; }
  python3 -W ignore "$S/kw_render.py" $n > out/$nn.log2 2>&1 || { echo "FAIL2 $n"; continue; }
  o=$(ls out/${nn}_*.mp4 | head -1); cp "$o" "$DST/"
  echo "DONE $n -> $DST/$(basename "$o")"; grep -E "табылмады|камерада емес|video" out/$nn.log2
done
echo ALLDONE
