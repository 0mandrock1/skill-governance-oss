# CC capabilities map

Що згенерований промпт може закладати як доступне в Claude Code (станом на 2026). Тримати на рівні **категорій**, не версій — версійні дрібниці rot-яться; за специфікою слати в `https://docs.claude.com`. Перевіряти актуальність перед тим, як зашивати щось точне.

## Модель
- Дефолт у Claude Code — **Opus 5** (замінив Opus 4.8). Є fast mode (до 2.5× швидше, преміум-ціна) і `--fallback-model` на випадок відсутності основної. `/model` міняє модель лише для поточної сесії. Точний вибір моделі/effort для артефакту — через `model-router` (Режим B), не тут.
- Для промпта: модель зазвичай не зашивати всередину артефакту — decision card `model-router` іде окремим блоком перед ним; згадати fast mode лише якщо задача масова й проста.

## Розширення (canonical packaging)
- **Plugin** — версійований бандл: скіли + сабагенти + slash-команди + хуки + output styles + MCP-визначення одним інсталом. `/plugin` для браузингу; офіційний marketplace `claude-plugins-official`.
- **Skill** — markdown-директорія, вантажиться прогресивно й контекстно; портативна між Claude Code / SDK / іншими агентами.
- **Subagent** — окрема Claude-сесія через Task/Agent tool: власний контекст, власний список тулів, опційна ізоляція. `CLAUDE_CODE_FORK_SUBAGENT=1` для non-interactive.
- **Output styles** — markdown-файл (frontmatter `name`/`description`/`keep-coding-instructions`) у `~/.claude/output-styles/` (юзер) чи `.claude/output-styles/` (проєкт); перемикання через `/config` або ключ `outputStyle` у settings-файлі. Для headless `claude -p` без чіпання спільного `settings.json` — `--settings '{"outputStyle":"<name>"}'` саме на цей ран.
- **Hooks** — PreToolUse / PostToolUse (PostToolUse може замінювати вивід тула), плюс statusLine.

## Workflow (нове)
- **Workflow** — оркестраційний скрипт, який Claude пише під задачу і ганяє по багатьох сабагентах **у фоні**. Для великих багатокрокових задач замість одного лінійного прогону. Закладати, коли задача природно б'ється на паралельні підзадачі.

## Фонові джоби
- Довгі shell-команди — `run_in_background`; агент отримує нотифікації про завершення й поллить вивід не блокуючись. `/resume` підтримує фонові сесії.

## MCP
- Tool-search deferral за замовчуванням (тули вантажаться по потребі). `alwaysLoad: true` у конфізі сервера — всі тули скіпають deferral і завжди доступні. Багато MCP-серверів разом топлять контекст — у промпті називати потрібні поіменно, не «підключи все».

## Browser (Mark-specific)
- Браузерне розширення Марка підключене на **Edge на всіх його десктопах** (Windows/Linux), не на мобільних. Тобто browser-автоматизація — реальна capability на будь-якому десктопі: run-and-verify (відкрити застосунок і перевірити зміну вживу), скрейпінг, перевірка UI. Вибір браузера — через connected-browsers. Не закладати на мобільних.

## Приклад заповненого середовища (для ілюстрації, не інструкція)
- Агенти: claudekit (triage/code-review/refactoring/research/code-search/documentation/database/testing/typescript/react/nestjs/kafka/loopback/ai-sdk) + VoltAgent (php-pro/laravel/python/sql/postgres/security/llm-architect/mcp-developer/payment). VPS-агенти (`~/.claude/agents` на node-a) — окрема сімʼя, tools-inheritance й розгортання через `vps-agent-creator`, не claudekit/VoltAgent.
- Команди (~/.claude/commands/): checkpoint:*, git:*, code-review, validate-and-fix, spec:create/execute, research, create-subagent, agents-md:init (джерело: carlrannaberg/claudekit).
- WSL: Windows-файли через `/mnt/c/Users/...`.
- Стек: PHP 8.4/Laravel/PostgreSQL, FusionPBX. Linux Ubuntu 24 (робота), Windows 11 (дім).
