# source ~/maxkallaway-kit/env.sh — әр Bash командасының басында (shell күйі сақталмайды)
#   E = engine, CREO_HOME = <пайдаланушы репосы>/maxkallaway (kit өз ішінде іске қосылса — kit түбірі)
K="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"; export E="$K/engine"
R="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ "$R" = "$K" ]; then export CREO_HOME="$K"; else export CREO_HOME="$R/maxkallaway"; fi
mkdir -p "$CREO_HOME"/{inbox,projects,ready}
[ "$CREO_HOME" != "$K" ] && [ ! -f "$CREO_HOME/.gitignore" ] && printf 'inbox/\nprojects/*/audio/\nprojects/*/chunks/\nprojects/*/out/\nprojects/*/test/\nprojects/*/src/\n' > "$CREO_HOME/.gitignore"
true
