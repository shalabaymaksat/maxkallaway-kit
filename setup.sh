#!/bin/bash
# Бұлттағы Claude Code сессиясында бір рет: ffmpeg + Python кітапханалары + жергілікті Whisper (API кілт керек емес)
set -e
if ! command -v ffmpeg >/dev/null; then
  (sudo -n true 2>/dev/null && SUDO=sudo) || SUDO=
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg >/dev/null
fi
python3 -m pip install -q --disable-pip-version-check numpy pillow requests faster-whisper gdown 2>&1 | tail -2 || true
python3 -c "import PIL, numpy, requests, faster_whisper, gdown; print('setup OK')"
ffmpeg -version | head -1
