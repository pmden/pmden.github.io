#!/bin/bash
# Автоматичний пошук дефектів у мобільній збірці. 8 правил:
# overflow · chrome-leak · chrome-text · escaped-html · unstyled-link
# dead-button · dead-link · table-overflow · text-clip
# Запуск:  ./check.sh [порт]   (за замовчуванням 8791)
PORT=${1:-8791}
B="$HOME/.claude/skills/gstack/browse/dist/browse"
D="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)
$B viewport 390x844 >/dev/null 2>&1
ls "$D"/*.html | sed "s|$D/||" > "$TMP/pages.txt"
: > "$TMP/out.jsonl"
while read -r v; do
  $B goto "http://localhost:$PORT/mobile-v1/$v" >/dev/null 2>&1
  r=$($B eval "$D/check.js" 2>/dev/null | grep -o '{.*}' | head -1)
  [ -n "$r" ] && echo "{\"page\":\"$v\",\"r\":$r}" >> "$TMP/out.jsonl"
done < "$TMP/pages.txt"
python3 - "$TMP/out.jsonl" <<'PY'
import json,sys,collections
rows=[json.loads(l) for l in open(sys.argv[1])]
agg=collections.Counter(); pages=collections.defaultdict(set); ex=collections.defaultdict(set)
for r in rows:
    for k,v in r['r'].items():
        agg[k]+=v['n']; pages[k].add(r['page'])
        for e in v['ex']: ex[k].add(e)
print(f"перевірено сторінок: {len(rows)}")
if not agg: print("ДЕФЕКТІВ НЕ ЗНАЙДЕНО"); raise SystemExit(0)
for k,n in agg.most_common():
    print(f"\n{k}: {n} на {len(pages[k])} стор.")
    for e in list(ex[k])[:3]: print("   ",e)
    print("   ", sorted(pages[k])[:3])
PY
