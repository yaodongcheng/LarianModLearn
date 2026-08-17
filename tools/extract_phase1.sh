#!/bin/bash
# Phase 1: targeted extraction of BG3 + DOS2 game data for LLM-NPC-AI analysis
DIVINE="/f/LarianModLearn/tools/ExportTool-v1.20.4/Packed/Tools/Divine.exe"
BG3="E:\\SteamLibrary\\steamapps\\common\\Baldurs Gate 3\\Data"
DOS2="G:\\SteamLibrary\\steamapps\\common\\Divinity Original Sin 2\\DefEd\\Data"
OUT_BG3="f:\\LarianModLearn\\extracted\\BG3"
OUT_DOS2="f:\\LarianModLearn\\extracted\\DOS2"

extract() {
  local game=$1 pak=$2 pat=$3 out=$4 tag=$5
  echo "=== $tag: $pak :: $pat ==="
  "$DIVINE" -g "$game" --action extract-package -s "$pak" -x "$pat" -d "$out" > /dev/null 2>&1 && echo "OK $tag" || echo "FAIL $tag"
}

# ---- BG3 ----
extract bg3 "$BG3\\Shared.pak" "**/Story/**" "$OUT_BG3" "BG3 Shared Story"
extract bg3 "$BG3\\Shared.pak" "**/Stats/**" "$OUT_BG3" "BG3 Shared Stats"
extract bg3 "$BG3\\Shared.pak" "**/Flags/**" "$OUT_BG3" "BG3 Shared Flags"
extract bg3 "$BG3\\Shared.pak" "**/Scripts/**" "$OUT_BG3" "BG3 Shared Scripts"
extract bg3 "$BG3\\Shared.pak" "**/Localization/**" "$OUT_BG3" "BG3 Shared Localization"
extract bg3 "$BG3\\Gustav.pak" "**/Story/**" "$OUT_BG3" "BG3 Gustav Story"
extract bg3 "$BG3\\Gustav.pak" "**/Flags/**" "$OUT_BG3" "BG3 Gustav Flags"
extract bg3 "$BG3\\Gustav.pak" "**/ApprovalRatings/**" "$OUT_BG3" "BG3 ApprovalRatings"
extract bg3 "$BG3\\Gustav.pak" "**/Stats/**" "$OUT_BG3" "BG3 Gustav Stats"
extract bg3 "$BG3\\Gustav.pak" "**/Timeline/**" "$OUT_BG3" "BG3 Gustav Timeline"
extract bg3 "$BG3\\Gustav.pak" "**/TimelineTemplates/**" "$OUT_BG3" "BG3 TimelineTemplates"
extract bg3 "$BG3\\Patch8_HotFix9.pak" "**/Story/**" "$OUT_BG3" "BG3 Patch8 Story"
extract bg3 "$BG3\\Game.pak" "Scripts/**" "$OUT_BG3" "BG3 Game Scripts"
echo "=== BG3 DONE ==="

# ---- DOS2 DE ----
extract dos2de "$DOS2\\Shared.pak" "**/Story/**" "$OUT_DOS2" "DOS2 Shared Story"
extract dos2de "$DOS2\\Shared.pak" "**/Stats/**" "$OUT_DOS2" "DOS2 Shared Stats"
extract dos2de "$DOS2\\Shared.pak" "**/Scripts/**" "$OUT_DOS2" "DOS2 Shared Scripts"
extract dos2de "$DOS2\\Shared.pak" "**/Content/**" "$OUT_DOS2" "DOS2 Shared Content"
extract dos2de "$DOS2\\Shared.pak" "**/AI/**" "$OUT_DOS2" "DOS2 Shared AI"
extract dos2de "$DOS2\\Shared.pak" "**/Globals/**" "$OUT_DOS2" "DOS2 Globals"
extract dos2de "$DOS2\\Shared.pak" "**/Localization/**" "$OUT_DOS2" "DOS2 Localization"
extract dos2de "$DOS2\\Game.pak" "**/Content/**" "$OUT_DOS2" "DOS2 Game Content"
extract dos2de "$DOS2\\Origins.pak" "**/Story/**" "$OUT_DOS2" "DOS2 Origins Story"
extract dos2de "$DOS2\\Origins.pak" "**/Stats/**" "$OUT_DOS2" "DOS2 Origins Stats"
extract dos2de "$DOS2\\Patch10.pak" "**/Story/**" "$OUT_DOS2" "DOS2 Patch10 Story"
echo "=== DOS2 DONE ==="

echo "--- file counts ---"
find "/f/LarianModLearn/extracted/BG3" -type f | wc -l
find "/f/LarianModLearn/extracted/DOS2" -type f | wc -l
du -sh "/f/LarianModLearn/extracted/BG3" "/f/LarianModLearn/extracted/DOS2"
