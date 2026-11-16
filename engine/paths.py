import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FF = shutil.which('ffmpeg') or 'ffmpeg'
ASSETS = ROOT + 'assets/'
FONTS = ROOT + 'fonts/'
MODEL = ROOT + 'models/selfie_multiclass.tflite'
# Пайдаланушының жұмыс папкасы (өз репосы ішінде, мыс. <репо>/creofast). Берілмесе — осы kit-тің түбірі.
HOME = os.path.abspath(os.environ.get('CREO_HOME') or ROOT).rstrip('/') + '/'
MY = HOME + ('assets/my/' if HOME == ROOT else 'assets/')   # өз B-roll активтері
