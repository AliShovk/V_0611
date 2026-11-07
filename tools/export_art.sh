#!/usr/bin/env bash
# Пакетный экспорт SVG -> PNG (2x) через Inkscape.
set -e
INK="${INKSCAPE:-inkscape}"
[ -x "/c/Program Files/Inkscape/bin/inkscape.exe" ] && INK="/c/Program Files/Inkscape/bin/inkscape.exe"

# имя_файла:ширина_экспорта
for pair in space_bg:1440 storm_bg:1440 cordyceps_bg:1440 venus:1000 venus_face:720 \
            bolt:560 sun:520 mercury:420 ant:760 stalk:360 cordyceps_stalk:360 \
            cordyceps_wound:400; do
  name="${pair%%:*}"; width="${pair##*:}"
  [ -f "art/$name.svg" ] || continue
  echo "-> art/$name.png (${width}px)"
  "$INK" --export-type=png --export-filename="art/$name.png" --export-width="$width" "art/$name.svg" >/dev/null
done
echo "готово"
