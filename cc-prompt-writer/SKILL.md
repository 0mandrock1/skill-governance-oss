---
name: cc-prompt-writer
description: >
  Генерує промпти/конфіги для Claude Code через короткий інтерв'ю: CLAUDE.md (контекст проєкту),
  дефініції сабагентів (~/.claude/agents/), one-off task-промпти для CLI/non-interactive прогонів.
  Знає поточні можливості Claude Code (Opus 5 дефолт, plugins як бандл, workflows у фоні,
  subagents, hooks, background jobs, MCP tool-search, browser-автоматизація через Edge на десктопах)
  і середовище Марка (claudekit + VoltAgent агенти, WSL-шляхи, PHP/Laravel/Postgres стек).
  Trigger: "напиши промпт для claude code", "зроби CLAUDE.md", "склади агента", "task prompt для cc",
  "create claude code prompt", "/cc-prompt-writer", або коли Mark описує проєкт/задачу і хоче
  сконфігурувати Claude Code.
  НЕ trigger: для Cowork — там cowork-prompt і його інстанси (інший рантайм: конектори/скіли/
  воркспейс, не CLI/файли/git). Cowork ≠ Claude Code. Для сабагента, що має реально ЖИТИ на VPS
  (симлінк + git-коміт у claude-config, а не просто текст) — `vps-agent-creator`, не цей скіл.
---

# CC Prompt Writer

## Step 0 — MANDATORY

Read `skill-creator-framework` (його `SKILL.md`) повністю в цій сесії, перш ніж
торкатися будь-якого `SKILL.md`. Тригер-простір і контракти спільні — навіть
правка одного рядка ламає колекцію тихо.

Наприкінці, перш ніж вважати зміну готовою, прогнати три лінти й показати FAIL-и
(без відкритих FAIL — не комітити):

```sh
python3 skill-creator-framework/scripts/validate_registry.py --skills . --registry <private state-registry.md>
python3 skill-creator-framework/scripts/lint_dependencies.py --skills .
python3 skill-creator-framework/scripts/audit_triggers.py  --skills .
```


Генерує артефакти для **Claude Code** — CLI/файлового агента: CLAUDE.md, дефініції сабагентів, one-off task-промпти.

Optionally reads a `model-router` skill from your own collection, if you have one (Режим B —
вибір моделі/effort для артефакту, і verbatim self-check блок для Режиму 2). Not shipped in
this repository — Режим B degrades to asking the user directly when it is absent.

## Чому окремий скіл, не інстанс cowork-prompt

Той самий *підхід* (єдине джерело constraints + фіксований шаблон + щільний інтерв'ю), але **інший рантайм**. Claude Code = файли, git, термінал, сабагенти, CLAUDE.md, плагіни. Cowork = конектори, скіли, воркспейс, tool-apps. Constraints різні (тут — reading rules / `/code-search` / git; там — confirm-before на конекторах). І виходів тут **три** (CLAUDE.md / agent / task), а не один. Тому sibling, не child cowork-prompt. Спільні лише принципи, не файли.

## Підхід (новий)

1. Визначити **режим виходу**: CLAUDE.md / subagent / task-промпт. Якщо неясно з запиту — спитати одним питанням.
2. Щільний інтерв'ю під режим (нижче). Що Mark сказав — не перепитувати. Дефолти застосовувати і називати.
3. Перед закладанням точних можливостей CC — звіритися з `references/cc-capabilities.md` (категорії) і за специфікою з `https://docs.claude.com`, бо фічі швидко змінюються.
4. **Модель для артефакту** — прочитати `model-router/SKILL.md` (Режим B, контракт "Виклик з іншого скілу"), застосувати логіку вибору й винести decision card (`Модель · Effort · Інструмент`) **першим блоком** перед самим артефактом. Не зашивати модель усередину CLAUDE.md/task-промпту (агент бере дефолт вузла), decision card — окремо, для Mark.
5. Заповнити шаблон режиму.
6. Вставити блок із `references/cc-constraints.md` **дослівно** (token-opt + reading rules).
7. Режим 2 додатково — вставити `model-router/references/self-check-block.md` **дослівно** (див. нижче).
8. Видати готовий артефакт без обгорток.

## Що нового в CC — закладати доречно (деталі: cc-capabilities.md)

- **Plugins** — якщо Mark створює переборний набір (агенти+команди+хуки+скіли), пропонувати запакувати як plugin, а не розсип файлів.
- **Workflows** — для великих задач, що б'ються на паралельні підзадачі: оркестрація по сабагентах у фоні замість лінійного прогону.
- **Subagents / hooks / background jobs / MCP `alwaysLoad`** — закладати під задачу.
- **Browser-автоматизація** — Edge Марка підключений на всіх десктопах: для run-and-verify, скрейпу, перевірки UI. Не на мобільних.
- **Opus 5** — дефолт Claude Code; модель зазвичай не зашивати в сам артефакт (decision card — окремо, крок 4 вище), fast mode — лише для масово-простих задач.

## Режим 1 — CLAUDE.md

Контекст проєкту, що Claude Code читає на старті. Інтерв'ю: стек і структура репо; команди (білд/тест/лінт/міграції); конвенції (стиль, патерни, чого не робити); які агенти/команди задіяти; MCP-сервери проєкту.

Шаблон:
```
# <Проєкт>
## Стек
<мови, фреймворки, БД>
## Структура
<ключові директорії, точки входу>
## Команди
<build / test / lint / migrate — точні рядки>
## Конвенції
<стиль, патерни, заборони>
## Агенти / команди
<які claudekit/VoltAgent сабагенти і коли; релевантні /команди>
## MCP
<сервери проєкту, alwaysLoad якщо треба>

<блок із cc-constraints.md дослівно — окремим розділом>
```

## Режим 2 — Subagent (~/.claude/agents/)

Роль-дефініція сабагента. Інтерв'ю: одна чітка відповідальність; які тули можна (звузити список — менший контекст); коли parent його кличе; критерій готовності.

Шаблон:
```
---
name: <agent-name>
description: <коли parent делегує сюди — конкретно й «пушливо»>
tools: <звужений список; менше = дешевше>
---
# Роль
<одна відповідальність>
# Коли запускати
<тригери делегування від parent>
# Як працювати
<підхід, межі, чого не робити>

## Model self-check (model-router Режим C)
<verbatim з model-router/references/self-check-block.md — не переказувати своїми словами>

# Done
<критерій завершення>

<блок із cc-constraints.md дослівно>
```

Не дублювати наявних агентів Марка (claudekit + VoltAgent — див. cc-capabilities.md); якщо роль уже покрита — сказати і не плодити.

**Це текстовий артефакт для ручної вставки.** Якщо задача — реально розгорнути
агента на VPS живим файлом (симлінк із `claude-config`, git-коміт, tools-
inheritance від базового мандрок-агента) — це `vps-agent-creator`, не цей режим.
Різниця: тут Mark сам зберігає файл; там скіл сам пише, симлінкає й комітить.

## Режим 3 — One-off task prompt

Разовий промпт для CLI/non-interactive (`claude -p`) чи інтерактивної задачі. Інтерв'ю: ціль (результат); які файли/директорії в скоупі; крок-перевірка (тест/білд/run); чи варто workflow (велика/паралельна) чи лінійно.

Шаблон:
```
## Goal
<результат, не кроки>
## Scope
<файли/директорії в межах; out-of-scope>
## Approach
<кроки або «workflow по сабагентах», якщо велика>
## Verify
<як підтвердити: тест/білд/run; browser run-and-verify якщо UI>
## Done
<критерій>

<блок із cc-constraints.md дослівно>
```

## Якість

- Ціль — результат, не процес. Scope з явним out-of-scope.
- Тули/агенти/MCP — поіменно; «підключи все» топить контекст.
- Артефакт самодостатній: вставив у чистий CC — спрацює.
- Decision card моделі (крок 4) — завжди перед артефактом, ніколи не всередині нього.
- WSL-шляхи Марка — `/mnt/c/Users/...`, коли проєкт на Windows-боці.

## Public Interface (Inter-Skill API)
- `cc_prompt_writer.task_prompt(spec) → prompt_md` — зібрати one-off task-промпт для CC-рану.
- `cc_prompt_writer.claude_md(project) → md` — CLAUDE.md для проєкту.

Скіл stateless — генерує текст, персистентного стану не тримає, `## Encapsulation` не потрібна.
