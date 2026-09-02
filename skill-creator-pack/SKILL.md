---
name: skill-creator-pack
description: >
  Пакує ОДИН скіл у distributable `.skill`-архів через штатний
  `package_skill.py` зі skill-creator, попередньо нормалізувавши frontmatter під
  офіційну схему Agent Skills (переносить нестандартні ключі на кшталт `version:`
  під `metadata:`, інакше валідація падає і пакування не відбувається).
  Trigger коли Mark каже: "запакуй скіл", "зроби .skill", "збери скіл в архів",
  "запакуй як skill-creator", "віддай скіл файлом", "skill-creator-pack",
  "/skill-creator-pack", або коли скіл щойно відредаговано і його треба віддати
  назовні одним файлом. НЕ trigger: пачка скілів, що змінились разом, в один
  бандл — це `skill-creator-set`; синхронізація живих скілів з бекап-репою —
  `skills-sync`; авторинг, евали і тюнінг description — `skill-creator`
  (він читає `skill-creator-framework` першим); експорт скіла на інші платформи
  (ChatGPT/Gemini/Grok) — `skill-translator`.
---

# skill-creator-pack

Один скіл → один валідний `.skill`.

External tool (не skill-залежність цієї колекції): `skill-creator` example (`scripts/package_skill.py`)
Internal scripts: `scripts/package_skill.py`, `scripts/quick_validate.py`
Overrides: додає крок нормалізації frontmatter перед валідацією
Reuses verbatim: формат архіву, правила виключення (`__pycache__`,
`node_modules`, `*.pyc`, `.DS_Store`, кореневий `evals/`)

> `skill-creator` живе в `/mnt/skills/examples/`, тобто постачається Anthropic і
> не контролюється цією колекцією. Тому це `Depends on:`, а не `Inherits from:` —
> лінти колекції його не бачать і не можуть гарантувати контракт. Якщо апстрим
> змінить `package_skill.py` або список ALLOWED, ламається саме цей скіл;
> перевіряти при кожному оновленні середовища.

**Крок 0:** прочитати скіл `skill-creator-framework` (його `SKILL.md`) повністю —
обов'язково перед будь-якою роботою з SKILL.md, включно з нормалізацією.

---

## Навіщо цей шар

`package_skill.py` валідує frontmatter проти закритого списку ключів:
`name, description, allowed-tools, compatibility, license, metadata`.

`skill-creator-framework` §7 при цьому **вимагає** `version:` у frontmatter для
кожного скіла, що володіє стейтом. Ці два правила прямо суперечать одне одному,
і в реальній колекції через це не пакується 6 скілів — саме базових
(`doc-store-poster`, `channel-poster`, `channel-poster-personal`,
`cc-remote-agent-node-b`, `model-router-runfile`, `skill-creator-framework`).

Скіл розв'язує конфлікт на користь платформи: ключ не втрачається, а їде під
`metadata:`, де схема його приймає, а фреймворкова конвенція лишається читабельною.

---

## Процедура

1. **Копія.** Скіли в `/mnt/skills/` read-only. Скопіювати теку в writable
   (`/home/claude/skills/<name>`), `chmod -R u+w`. Правити оригінал не можна.
2. **Нормалізація.**
   ```
   python scripts/normalize_frontmatter.py /home/claude/skills/<name> --check
   ```
   Якщо повідомляє про ключі — прогнати без `--check`. Що саме поїхало під
   `metadata:` — сказати Марку рядком, не мовчки.
3. **Пакування.**
   ```
   cd /mnt/skills/examples/skill-creator
   python -m scripts.package_skill /home/claude/skills/<name> /home/claude/dist
   ```
4. **Верифікація.** `unzip -l` архіву: у списку мусить бути `SKILL.md` і всі
   `references/`, `scripts/`, `assets/`. Порожній або на один файл там, де в
   скіла є bundled resources — це провал, а не успіх.
5. **Віддача.** `present_files` на `.skill`. Якщо в одному заході пакується
   кілька — не давати їм колідувати по імені у виході.

---

## Inter-Skill API

### Owns
Нічого. Скіл stateless — читає теку скіла, пише артефакт у `dist`.
Артефакт ефемерний, не персистентний стейт.

### Public Interface (Inter-Skill API)
- `skill-creator-pack.pack(skill_dir, dist_dir?) → path_to_skill_file` —
  копія → нормалізація → валідація → zip. Кидає помилку, якщо валідація не
  пройшла після нормалізації (тобто проблема не в `version:`, а глибша).
- `skill-creator-pack.normalize(skill_dir, check?) → [moved_keys]` — лише крок 2,
  без пакування. Для аудиту колекції.

### Internal (do not call from outside)
- _парсинг frontmatter, порядок ключів у вихідному YAML, правила відступів,_
  _список ALLOWED (він належить платформі, не цьому скілу)._

---

## Gotchas

- **Нормалізація змінює файл.** Тому крок 1 не опційний: без копії скіл
  редагується на місці, а в `/mnt/skills/` це або відмова, або зіпсований
  оригінал у live-акаунті.
- **Валідація ловить не тільки frontmatter.** `name` мусить збігатися з іменем
  теки, `description` ≤ 1024 символи, рівно один `SKILL.md` у пакованому дереві.
  Нормалізація цього не лікує — це правки в тексті скіла.
- **`.skill` — це zip.** Перевіряти вміст, а не факт створення файлу.
- **Кореневий `evals/` не пакується.** Якщо тести мають поїхати разом зі скілом —
  вони не в `evals/`.
- Прогнати `python scripts/audit_triggers.py` зі `skill-creator-framework` після
  будь-якої правки description — цей скіл сидить у щільному кутку тригерного
  простору (`skill-*` × 7).
