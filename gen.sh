#!/usr/bin/env bash
# Запуск эпизода Vgen: ./gen.sh venus_hook  → storage/cartoon-venus-hook/final.mp4
# Без аргумента — список доступных эпизодов.
set -euo pipefail
cd "$(dirname "$0")"

export FONT_BOLD="${FONT_BOLD:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}"
export FFMPEG="${FFMPEG:-/usr/bin/ffmpeg}"

if [ $# -eq 0 ]; then
  echo "Доступные эпизоды:"
  ls scripts/cartoon_*.py | sed 's#scripts/cartoon_##; s#\.py$##' | sed 's/^/  /'
  exit 0
fi

ep="${1#cartoon_}"; ep="${ep%.py}"
script="scripts/cartoon_${ep}.py"
[ -f "$script" ] || { echo "Нет эпизода: $ep"; exit 1; }

echo "Запуск $script"
./.venv/bin/python "$script"
echo "Готово: storage/cartoon-${ep}/final.mp4"
