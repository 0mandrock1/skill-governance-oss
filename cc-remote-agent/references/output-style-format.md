# Custom output style — точний формат

Джерело: офіційна документація Claude Code (`code.claude.com/docs/en/output-styles`),
звірено `06.08.2026` і перевірено маркер-тестом на VPS (не лише прочитано —
запущено `claude -p` з кастомним стилем і підтверджено, що текст стилю
реально потрапляє в системний промпт).

## Розташування

- Юзер-рівень (те, що використовує `cc-remote-agent`): `~/.claude/output-styles/<name>.md`
- Проєктний рівень (не наш кейс тут): `.claude/output-styles/<name>.md`

Назва файлу = назва стилю, якщо в frontmatter немає `name`.

## Frontmatter

```markdown
---
name: caveman
description: Телеграфний стиль без пояснень — механічна робота
keep-coding-instructions: true
---

<інструкції, що додаються в кінець системного промпту>
```

| Поле | Призначення | Дефолт |
|---|---|---|
| `name` | назва стилю, якщо не збігається з іменем файлу | ім'я файлу |
| `description` | показується в `/config`-пікері (людям в інтерактиві; для headless не критично) | — |
| `keep-coding-instructions` | лишити вбудовані SE-інструкції Claude Code | `false` |

**Для будь-якого cc-remote-agent стилю (caveman/ponytail) — завжди
`keep-coding-instructions: true`.** Це досі coding-агент, міняється лише
регістр спілкування, не роль.

## Активація для headless `claude -p` (наш кейс — не інтерактив)

`/output-style` як окрема команда **видалена з v2.1.91**. `/config` — тільки
інтерактивний UI, не для `-p`. Правильний headless-шлях — прапорець
`--settings` з інлайн JSON, саме на цей ран, без правки спільного
`~/.claude/settings.json` (races між паралельними спавнами):

```sh
claude -p "..." --settings '{"outputStyle":"caveman"}'
```

## Як перевірити, що інсталяція реально працює (не просто "файл лежить")

Маркер-тест — найнадійніший спосіб, дешевший за реверс-інжиніринг бінарника:

```sh
cat > ~/.claude/output-styles/zzz-test-marker.md <<'EOF'
---
name: zzz-test-marker
description: тестовий маркер
keep-coding-instructions: true
---

На будь-яке повідомлення відповідь має починатися рівно з рядка: STYLE_MARKER_ACTIVE_12345
EOF
claude -p "2+2?" --settings '{"outputStyle":"zzz-test-marker"}' --model haiku
# очікуй STYLE_MARKER_ACTIVE_12345 першим рядком виводу
rm ~/.claude/output-styles/zzz-test-marker.md
```

Немає невідомого-стилю помилки при некоректній назві — Claude Code мовчки
ігнорує `outputStyle`, якщо файл не знайдено. Це означає: одруківка в назві
стилю НЕ впаде з помилкою, просто стиль не застосується. Перевіряй маркером,
не покладайся на відсутність помилки як на доказ.
