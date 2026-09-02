#!/bin/sh
# Обгортка ОДИНОЧНОГО cc-рану: claude -p → витяг RESULT з out.log → нотифікація.
# Ланцюг має свою нотифікацію в cc-chain.sh; це — та сама точка для ранів поза
# ланцюгом, щоб обіцянка «будь-який ран нотифікує» була правдою, а не текстом.
#
#   sh cc-run.sh <run-dir> [style] [model]
#     <run-dir>  тека рану, у якій ВЖЕ лежить task.md
#     style      ponytail | caveman | none (дефолт none = без --settings)
#
# ENV: CC_TOOLS  (дефолт "Bash Edit Write Read Glob Grep")
#      CC_NOTIFY (дефолт <runs>/cc-notify.sh; нема файлу — нотифікація тихо
#                 пропускається, ран від цього не падає)
#      CC_TAG    (префікс у повідомленні, дефолт "run")
#
# Коди виходу: 0 ok | 2 fail (нема RESULT: ok) | 3 session limit
set -u

D=${1:?run-dir}; D=${D%/}
STYLE=${2:-none}
MODEL=${3:-}
[ -f "$D/task.md" ] || { echo "cc-run: нема $D/task.md" >&2; exit 1; }

RUNS=$(dirname "$D")
ID=$(basename "$D")
TOOLS=${CC_TOOLS:-"Bash Edit Write Read Glob Grep"}
NOTIFY=${CC_NOTIFY:-$RUNS/cc-notify.sh}
TAG=${CC_TAG:-run}
MODELARG=""; [ -n "$MODEL" ] && MODELARG="--model $MODEL"

# --- Гард дорогої моделі (exit 6) ---
# opus без CC_OPUS_REASON не стартує. Стоїть ДО спавна, тому відмова
# коштує нуль токенів. Відсутність гарду на вузлі — не помилка рану.
if [ -f "$RUNS/cc-opus-gate.sh" ]; then
  sh "$RUNS/cc-opus-gate.sh" "$MODEL" "$ID" || exit $?
fi

# Best-effort: нотифікація ніколи не валить ран і не чіпає код виходу.
notify(){ [ -f "$NOTIFY" ] || return 0; sh "$NOTIFY" "$*" >/dev/null 2>&1 || true; }

if [ "$STYLE" = "none" ]; then
  claude -p "$(cat "$D/task.md")" $MODELARG --permission-mode acceptEdits \
    --allowedTools "$TOOLS" < /dev/null > "$D/out.log" 2>&1
else
  claude -p "$(cat "$D/task.md")" $MODELARG --permission-mode acceptEdits \
    --allowedTools "$TOOLS" --settings "{\"outputStyle\":\"$STYLE\"}" < /dev/null > "$D/out.log" 2>&1
fi
RC=$?
echo "$RC" > "$D/exit_code"

# Юзедж рахуємо, якщо скрипт є на вузлі; його відсутність — не помилка рану.
[ -f "$RUNS/run-usage.sh" ] && sh "$RUNS/run-usage.sh" "$D" > "$D/usage.txt" 2>&1

# Вартість рану + sonnet-еквівалент у cost.log — best-effort, як і юзедж.
[ -f "$RUNS/cc-cost.sh" ] && sh "$RUNS/cc-cost.sh" "$D" >/dev/null 2>&1

# session limit — «прийди пізніше», окремий код, не провал задачі (як у ланцюзі).
if grep -aq "session limit" "$D/out.log" 2>/dev/null; then
  notify "$TAG $ID: SESSION LIMIT — ран не доїхав, прийди пізніше (exit 3)"
  exit 3
fi

# Той самий матчер, що й у cc-chain.sh: RESULT може приїхати обгорнутим у **.
LINE=$(tail -40 "$D/out.log" | grep -aE "RESULT:[[:space:]]*\**[[:space:]]*(ok|fail)" | tail -1)
NOTES=$(tail -40 "$D/out.log" | grep -aE "^[[:space:]]*\**[[:space:]]*NOTES:" | tail -1 | cut -c1-200)

if printf '%s' "$LINE" | grep -aqE "RESULT:[[:space:]]*\**[[:space:]]*ok"; then
  notify "$TAG $ID: ok${NOTES:+ — $NOTES}"
  exit 0
fi

if [ -n "$LINE" ]; then
  WHY="RESULT: fail"
else
  WHY="нема рядка RESULT у хвості логу"
fi
notify "$TAG $ID: fail (exit $RC, $WHY)${NOTES:+ — $NOTES}"
exit 2
