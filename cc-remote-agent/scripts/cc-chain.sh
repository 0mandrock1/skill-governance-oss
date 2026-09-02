#!/bin/sh
# Послідовний ланцюг Claude Code-ранів в ОДНІЙ робочій копії.
# Рани НЕ незалежні: кожен наступний продовжує гілку попереднього, тому вони
# йдуть строго один за одним. Ланцюг спиняється на першому рані без "RESULT: ok".
#
#   sh cc-chain.sh <cwd> <plan-file> [tag]
#
# Формат plan-файлу, по рядку на ран:   slug|style|/abs/path/task.md
#   style: ponytail | caveman | none | (порожньо/auto/будь-що інше =
#          авто-призначення π-цифрою за наскрізним індексом — рішення 24.08,
#          model-router-runfile/output-style-tracking; призначає вузол, не чат)
# У task.md плейсхолдер {RUN_ID} підставляється реальним id рану.
#
# Коди виходу: 0 пройшло все | 2 ран впав | 3 session limit ("прийди пізніше") | 4 конфлікт ізоляції (CWD чи plan вже зайнятий іншим ланцюгом) | 5 гейт тижневого бюджету / тижневий лок | 6 гард дорогої моделі
set -u
# --- Тижневий лок (крон cc-week-guard.sh) ---
# Присутній .week-locked -> тижневого бюджету менше порогу, cc-рани на VPS
# заглушено до скидання тижня. Дешева перевірка (без node/jq); знімає лок крон.
CWD=${1:?cwd}; PLAN=${2:?plan}; TAG=${3:-chain}
RUNS=${CC_RUNS:-$HOME/cc-runs}
WEEK_LOCK=${CC_WEEK_LOCK:-$RUNS/.week-locked}
if [ -f "$WEEK_LOCK" ]; then
  echo "ВІДМОВА: тижневий лок активний ($WEEK_LOCK) — cc-рани заглушено до скидання тижня" >&2
  exit 5
fi
STAMP=$(date +%Y%m%d-%H%M)
CHAIN=$RUNS/$TAG-$STAMP.log
TOOLS=${CC_TOOLS:-"Bash Edit Write Read Glob Grep"}

# --- Ізоляція: жоден інший ланцюг не має ділити CWD чи plan-файл одночасно ---
# Порушення (15.08): два cc-chain.sh на спільному plan-файлі в одній робочій
# копії виконали два рани двічі; другий прохід закомітив ті самі SHA що й
# перший (~73k out-токенів у нуль дифу). Тримається на mkdir-лок, не на дисципліні.
# ПРИМІТКА: `exec N>file` + `flock -n N` НЕ використовувати на цьому вузлі —
# перевірено вручну (`exec 200>/tmp/test.lock` валить "exec: 200: not found"
# у поточному /bin/sh на цій машині/транспорті). `flock -n LOCKFILE -c '...'`
# командною формою працює нормально, але mkdir атомарний і не залежить від
# flock узагалі — обрано його як найпростіший портативний варіант.
CWD_ABS=$(cd "$CWD" 2>/dev/null && pwd) || { echo "cwd не існує: $CWD" >&2; exit 1; }
PLAN_ABS=$(readlink -f "$PLAN" 2>/dev/null) || { echo "plan не існує: $PLAN" >&2; exit 1; }
LOCK_CWD="$RUNS/.lock-cwd-$(printf '%s' "$CWD_ABS" | md5sum | cut -c1-16).d"
LOCK_PLAN="$RUNS/.lock-plan-$(printf '%s' "$PLAN_ABS" | md5sum | cut -c1-16).d"
if ! mkdir "$LOCK_CWD" 2>/dev/null; then
  echo "ВІДМОВА: інший ланцюг вже працює в $CWD_ABS (lock $LOCK_CWD)" >&2
  exit 4
fi
if ! mkdir "$LOCK_PLAN" 2>/dev/null; then
  rmdir "$LOCK_CWD" 2>/dev/null
  echo "ВІДМОВА: інший ланцюг вже використовує $PLAN_ABS (lock $LOCK_PLAN)" >&2
  exit 4
fi
trap 'rmdir "$LOCK_CWD" "$LOCK_PLAN" 2>/dev/null' EXIT

log(){ echo "[$(date -u +%H:%M:%S)] $*" >> "$CHAIN"; }
# Best-effort Telegram-нотифікація; ніколи не валить ланцюг і не чіпає exit-коди.
# notify — afterflight (ok/fail/session/ланцюг), зі звуком, однорядковий телеграф.
# notify_silent — preflight (старт, <pre>-таблиця), без звуку (disable_notification).
notify(){ sh "$RUNS/cc-notify.sh" "$*" >/dev/null 2>&1 || true; }
notify_silent(){ sh "$RUNS/cc-notify.sh" "$1" silent >/dev/null 2>&1 || true; }
PASSED=0

# --- Протокол аромату (рішення 24.08) ---
# Порожнє/auto/будь-яке значення style, відмінне від трьох літералів нижче,
# призначається π-цифрою за наскрізним індексом — лічильник .style-index
# СПІЛЬНИЙ для всіх обгорток (лежить поза цим скриптом, у $RUNS), не
# скидається щобатчу: короткі батчі інакше систематично недобирають
# контрольну групу. digit mod 3 -> 0 caveman / 1 ponytail / 2 none.
# Явний style (caveman|ponytail|none) у plan-файлі — ручний override,
# лічильник НЕ чіпає. Призначення робить вузол, не чат-шар.
STYLE_DIGITS_FILE="$RUNS/.pi-digits"
STYLE_INDEX_FILE="$RUNS/.style-index"
STYLE_LOCK="$RUNS/.lock-style-index.d"
resolve_style(){
  in=$1
  case "$in" in
    caveman|ponytail|none) echo "$in"; return ;;
  esac
  n=0
  while ! mkdir "$STYLE_LOCK" 2>/dev/null; do
    n=$((n+1)); [ "$n" -gt 50 ] && break
    sleep 0.1
  done
  DIGITS=$(cat "$STYLE_DIGITS_FILE" 2>/dev/null)
  [ -n "$DIGITS" ] || DIGITS=31415926535897932384626433832795028841971693993751058209749445923078
  IDX=$(cat "$STYLE_INDEX_FILE" 2>/dev/null)
  case "$IDX" in ''|*[!0-9]*) IDX=0 ;; esac
  LEN=${#DIGITS}
  POS=$((IDX % LEN + 1))
  DIGIT=$(printf '%s' "$DIGITS" | cut -c"$POS")
  echo $((IDX + 1)) > "$STYLE_INDEX_FILE"
  rmdir "$STYLE_LOCK" 2>/dev/null
  case $((DIGIT % 3)) in
    0) echo caveman ;;
    1) echo ponytail ;;
    *) echo none ;;
  esac
}

do_run(){
  slug=$1; style=$2; task=$3; model=${4:-}
  MODELARG=""; [ -n "$model" ] && MODELARG="--model $model"
  # Гард дорогої моделі — на КОЖЕН крок ланцюга окремо: план може змішувати
  # sonnet і opus по рядках, тож перевірка мусить бути тут, а не на старті.
  if [ -f "$RUNS/cc-opus-gate.sh" ]; then
    sh "$RUNS/cc-opus-gate.sh" "$model" "$slug" || { log "$slug: opus-gate ВІДМОВА — ланцюг спинено"; exit 6; }
  fi
  id="$slug-$STAMP"; d="$RUNS/$id"; mkdir -p "$d"
  cd "$CWD" || exit 1
  git rev-parse HEAD > "$d/base_sha"
  git checkout -q -b "cc/$id" || { log "$id: не змогло створити гілку"; exit 1; }
  sed "s|{RUN_ID}|$id|g" "$task" > "$d/task.md"
  log "$id старт (style=$style, base=$(cut -c1-7 < $d/base_sha))"
  # CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0: без цього headless-сесія може
  # вийти по стелі очікування фонової задачі (Task/background bash),
  # обірвавши сесію ДО друку RESULT: — ран падає з реальною роботою
  # закомiченою, але формально FAIL (model-router-runfile SKILL.md
  # §Fan-out). Спрацювало 24.08 на tv2-time-preact: фоновий unit-test
  # batch, візуал-чек зелений, RESULT: так і не надрукувався.
  # RUN_TIMEOUT_S: жорсткий backstop поверх CEILING_MS вище — той лише робить
  # очікування видимим (один рядок у out.log), але сам по собі не обмежує
  # його в часі. Спрацювало 24.08 на tv2-rail: 26 хв, один рядок логу
  # "Waiting for background task notifications", реальна робота (228 рядків
  # rail.js) є, RESULT: так і не надрукувався. timeout не має нової семантики
  # для не-session-limit шляху: убитий процес так само не лишає "session
  # limit" у out.log і так само падає в гілку auto-commit -> FAIL нижче,
  # просто за фіксований час, а не за весь залишок вікна.
  RUN_TIMEOUT_S=${CC_RUN_TIMEOUT_S:-2700}
  if [ "$style" = "none" ]; then
    timeout "$RUN_TIMEOUT_S" env CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p "$(cat $d/task.md)" $MODELARG --permission-mode acceptEdits --allowedTools "$TOOLS" < /dev/null > "$d/out.log" 2>&1
  else
    timeout "$RUN_TIMEOUT_S" env CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p "$(cat $d/task.md)" $MODELARG --permission-mode acceptEdits --allowedTools "$TOOLS" --settings "{\"outputStyle\":\"$style\"}" < /dev/null > "$d/out.log" 2>&1
  fi
  CLAUDE_EXIT=$?
  [ "$CLAUDE_EXIT" = 124 ] && log "$id: TIMEOUT — вбито по ${RUN_TIMEOUT_S}s, перевіряю чи є реальна робота нижче"
  log "$(sh "$RUNS/run-usage.sh" "$d" 2>&1 | tail -1)"
  [ -f "$RUNS/cc-cost.sh" ] && log "$(sh "$RUNS/cc-cost.sh" "$d" 2>/dev/null | tail -1)"
  if grep -aq "session limit" "$d/out.log"; then
    log "$id: SESSION LIMIT — ланцюг спинено, це не провал задачі"
    echo 3 > "$d/exit_code"
    [ -f "$RUNS/cc-telemetry.sh" ] && sh "$RUNS/cc-telemetry.sh" "$d" run >/dev/null 2>&1
    notify "⛔ $TAG · session limit · <code>$id</code> · $PASSED ok до цього · exit 3"; exit 3
  fi
  if [ -n "$(git status --porcelain)" ]; then
    git add -A && git commit -qm "chore($slug): auto-commit run output" && log "$id: авто-коміт незакоміченого"
  fi
  if tail -40 "$d/out.log" | grep -aqE "RESULT:[[:space:]]*\**[[:space:]]*ok"; then
    log "$id: ok ($(git rev-parse --short HEAD))"
    echo 0 > "$d/exit_code"
    [ -f "$RUNS/cc-telemetry.sh" ] && sh "$RUNS/cc-telemetry.sh" "$d" run >/dev/null 2>&1
    PASSED=$((PASSED+1)); notify "✅ $TAG · run ok · <code>$(git rev-parse --short HEAD)</code> · пройдено $PASSED"
  else
    log "$id: FAIL — ланцюг спинено, гілка лишена як є для розбору"
    echo 2 > "$d/exit_code"
    [ -f "$RUNS/cc-telemetry.sh" ] && sh "$RUNS/cc-telemetry.sh" "$d" run >/dev/null 2>&1
    notify "❌ $TAG · run fail · <code>$id</code> · $PASSED ok до цього · exit 2 · гілку лишено"; exit 2
  fi
}

log "ланцюг стартував від $(git -C "$CWD" rev-parse --abbrev-ref HEAD)"
# Пре-фліт оцінка по першому кроку плану — грубий проксі на весь ланцюг (best-effort).
if [ -f "$RUNS/cc-estimate.sh" ]; then
  FIRST_LINE=$(grep -vE '^#|^$' "$PLAN" | head -1)
  FIRST_TASK=$(echo "$FIRST_LINE" | cut -d'|' -f3)
  FIRST_MODEL=$(echo "$FIRST_LINE" | cut -d'|' -f4)
  [ -n "$FIRST_MODEL" ] || FIRST_MODEL=sonnet
  N_STEPS=$(grep -vcE '^#|^$' "$PLAN")
  if [ -n "$FIRST_TASK" ] && [ -f "$FIRST_TASK" ]; then
    PREFLIGHT=$(sh "$RUNS/cc-estimate.sh" --task "$FIRST_TASK" --model "$FIRST_MODEL" --lanes "$N_STEPS" --maxpar 1 2>/dev/null)
    if [ -n "$PREFLIGHT" ]; then
      log "$PREFLIGHT"
      # Telegram отримує компактний HTML-блок; повний PREFLIGHT (з VARS) лишається в лозі ланцюга.
      PF_HTML=$(sh "$RUNS/cc-estimate.sh" --task "$FIRST_TASK" --model "$FIRST_MODEL" --lanes "$N_STEPS" --maxpar 1 --compact-html 2>/dev/null)
      if [ -n "$PF_HTML" ]; then
        notify_silent "<b>$TAG · старт ланцюга · $N_STEPS кроків</b>
$PF_HTML"
      else
        notify_silent "$TAG: старт ланцюга ($N_STEPS кроків) | $PREFLIGHT"
      fi
    fi
  fi
fi
# --- Гейт тижневого бюджету (25.08) ---
# Реальний % — з того самого офіційного джерела, що й бари /usage
# (usage-cli.js --ratelimit-json .util7d), не з оцінки cc-estimate.
# Ланцюг ВІДМОВЛЯЄТЬСЯ стартувати, якщо тижня лишилось менше порогу —
# структурна відсічка, яку не переговориш. Поріг CC_WEEK_MIN_LEFT (%, дефолт 5;
# 0 = вимкнути). Число недоступне -> fail-open (backstop лишається exit 3).
GATE_USAGE_CLI=${CC_USAGE_CLI:-$HOME/projects/usage-bot/usage-cli.js}
WEEK_MIN_LEFT=${CC_WEEK_MIN_LEFT:-5}
if [ "${WEEK_MIN_LEFT}" != 0 ] && command -v node >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 && [ -f "$GATE_USAGE_CLI" ]; then
  U7=$(node "$GATE_USAGE_CLI" --ratelimit-json 2>/dev/null | jq -r '.util7d // empty' 2>/dev/null)
  case "$U7" in
    ''|*[!0-9.]*) log "гейт тижня: util7d недоступний — fail-open, старт дозволено" ;;
    *)
      LEFT=$(awk -v u="$U7" 'BEGIN{printf "%.1f",(1-u)*100}')
      if awk -v l="$LEFT" -v m="$WEEK_MIN_LEFT" 'BEGIN{exit !(l<m)}'; then
        log "ГЕЙТ ТИЖНЯ: лишилось ${LEFT}% < ${WEEK_MIN_LEFT}% — ланцюг не стартував (exit 5)"
        notify "🚧 $TAG · гейт тижня · лишилось ${LEFT}% < ${WEEK_MIN_LEFT}% · не стартував · exit 5"
        exit 5
      fi
      log "гейт тижня: лишилось ${LEFT}% >= ${WEEK_MIN_LEFT}% — старт дозволено"
      ;;
  esac
fi
while IFS='|' read -r slug style_raw task model; do
  [ -n "${slug:-}" ] || continue
  case "$slug" in \#*) continue ;; esac
  style=$(resolve_style "$style_raw")
  [ "$style" = "$style_raw" ] || log "$slug: аромат авто-призначено π-цифрою -> $style"
  do_run "$slug" "$style" "$task" "${model:-}"
done < "$PLAN"
log "ланцюг пройшов повністю, гілка $(git -C "$CWD" rev-parse --abbrev-ref HEAD)"
notify "✅ $TAG · ланцюг пройшов · $PASSED ранів ok · гілка $(git -C "$CWD" rev-parse --abbrev-ref HEAD) · exit 0"
