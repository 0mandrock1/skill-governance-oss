---
name: skill-translator
description: >
  Translates one of Mark's Claude SKILL.md files into platform-native configs:
  ChatGPT Custom GPT (Instructions + Actions), Google Gemini Gem (Instructions +
  knowledge), Apple Shortcuts (deterministic workflow recipe), Grok custom
  instructions + xAI tool schema, DeepSeek system prompt + OpenAI-compatible
  tool schema, and a stubbed placeholder for GPT-6 Actions (spec doesn't exist
  yet — TBD template only, no invented details). Trigger on: "/skill-translator",
  "skill-translator", "переклади скіл на chatgpt/gemini/grok/deepseek/shortcuts",
  "зроби gem з цього скіла", "портуй скіл на іншу платформу", "custom gpt з
  нашого скіла", "експортуй скіл для grok/deepseek".
  NOT trigger: matching a raw idea to a skill — skill-rosetta; writing a human-facing
  methodology doc — skill-doc-framework.
---

# Skill Translator

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


Inherits from: skill-creator-framework (read first if modifying this skill itself).

---

## Reality Check — read before executing

One constraint doesn't disappear for any target platform: **MCP tools inside a
SKILL.md (Notion/Craft/kiri/Gmail/Calendar etc.) are private connectors
authorized under Mark's own Claude account.** No translation "activates" those
calls on ChatGPT/Grok/DeepSeek/Gemini/Shortcuts. Making them real requires Mark
to stand up a public HTTPS gateway with auth and describe *that* as an OpenAPI
schema — separate engineering work, not something this skill can automate.

So every translation splits a source SKILL.md into two layers:

1. **Portable layer** — triggers, decision logic, output formatting rules,
   style constraints, references to `references/`. This carries over almost
   1:1 into whatever the target platform calls its "Instructions"/"System
   prompt" field.
2. **Tool layer** — every MCP call. Translated as a **stub schema**
   (OpenAPI / function-calling JSON) with an explicit
   `# TODO: point at your own public gateway` — never as a working call.

Never export real credentials, tokens, or internal Notion/Craft IDs
into any output file. State Registry IDs from `skill-creator-framework` stay
internal.

---

## Platform Capability Matrix

| Platform | Instructions/prompt | Knowledge files | Tool/Action calling | Native workflow format |
|---|---|---|---|---|
| ChatGPT Custom GPT | ✅ Instructions field | ✅ up to 20 files | ✅ Actions = OpenAPI 3.1 schema | ❌ |
| Google Gemini Gem | ✅ Instructions field | ✅ Drive docs | ❌ (as of Jul 2026 — prompt+docs only, no custom Actions) | ❌ |
| Apple Shortcuts | ⚠️ only via an "Ask [Model]" step inside a workflow | ❌ | ✅ native actions (Get Contents of URL, HTTP Request) | ✅ this *is* the format |
| Grok (xAI) | ✅ Custom Instructions/Persona | ⚠️ limited | ✅ xAI API function calling (OpenAI-compatible tools schema) | ❌ |
| DeepSeek | ✅ system prompt via API | ❌ (no custom-GPT storefront) | ✅ OpenAI-compatible tools schema via API | ❌ |
| GPT-6 Actions | ❓ **spec doesn't exist (Jul 2026)** | ❓ | ❓ stub = copy of ChatGPT Actions format, marked TBD | ❓ |

If a claim here might be stale by the time this runs, verify with a quick web
search before generating the ChatGPT/Gemini/Grok/DeepSeek sections — platform
feature sets change faster than this table.

---

## Output Structure

For a source skill `{skill-name}`, generate:

```
/mnt/user-data/outputs/{skill-name}-translated/
├── chatgpt/
│   ├── instructions.md
│   ├── actions_openapi.yaml     (stub, TODO gateway)
│   └── knowledge/                (copy of references/, if any)
├── gemini_gem/
│   ├── instructions.md
│   └── knowledge/
├── shortcuts/
│   └── workflow.md               (step-by-step recipe — see Shortcuts note below)
├── grok/
│   ├── instructions.md
│   └── tools_schema.json
├── deepseek/
│   ├── system_prompt.md
│   └── tools_schema.json
└── gpt6_actions_stub/
    └── README.md                 (explicit TBD placeholder, mirrors chatgpt/actions_openapi.yaml)
```

Only generate the sub-folders the user actually asked for — don't pad output
with platforms nobody requested.

---

## Translation Steps

1. **Read source**: скіл `{skill-name}` (його `SKILL.md`) (+ `references/` if present).
2. **Split**: portable layer (triggers, decision logic, output rules, style) vs
   tool layer (every MCP call, every `Depends on:` line).
3. **Portable layer → Instructions**: rewrite the imperative SKILL.md body
   ("Read X", "Fetch Y") into 2nd-person system-prompt tone ("You are an
   assistant that..."). Strip internal filesystem paths
   (source skill dir), strip `## Encapsulation` and State Registry
   sections entirely — those are internal, not for an external platform.
4. **Tool layer → schema stub**: one OpenAPI path / function definition per
   MCP call, named after the owner-skill's Public Interface operation
   (`radar.recommend()` → `POST /radar/recommend`), each carrying
   `# TODO: replace with your own public endpoint`.
5. **references/ → knowledge**: copy as-is for ChatGPT/Gemini (native file
   upload). For Shortcuts/Grok/DeepSeek (no file upload) — inline the
   essential fragments directly into instructions/system_prompt instead.
6. **Shortcuts, specifically**: do not attempt to hand-generate a binary
   `.shortcut`/plist — Apple's format isn't safely authorable outside
   Shortcuts.app. Output a numbered, action-by-action recipe Mark assembles
   himself, or a `shortcuts://` x-callback-url snippet if the task reduces to
   one trivial HTTP call.
7. **Write files** per the Output Structure above.
8. **Present**: `present_files` on the concrete files produced (one meaningful
   file per platform), not the bare folder.

---

## Known Non-Portable Patterns

- Skills that are **fully** dependent on a stateful owner
  ([[radar]], `marvel-snap-deck`, [[personal-productivity-system]]) can't be
  translated with working read/write — only the "how to recommend/decide"
  prompt logic ports; the actual data layer doesn't exist on the target
  platform.
- Skills with `Inherits from: core` (all poster/publisher skills) —
  `creds.get()` and any credential handling never gets exported. The tool-layer
  stub for these is an empty placeholder, no real tokens, ever.
- The `ask_user_input_v0` button pattern has no native equivalent on
  ChatGPT/Gemini/Grok/DeepSeek — translate it as an ordinary clarifying
  question in prose.
- Anything relying on `visualize:show_widget`, `places_map_display_v0`, or
  other first-party interactive-widget tools has no equivalent anywhere else
  — drop it, note the loss explicitly to the user, don't silently omit it.

---

## Quick-Start Checklist

- [ ] Source `{skill-name}` exists in the collection
- [ ] Portable layer isolated (no internal paths, no Encapsulation/State Registry)
- [ ] Tool layer marked as stub with TODO gateway
- [ ] `references/` copied (ChatGPT/Gemini) or inlined (Shortcuts/Grok/DeepSeek)
- [ ] GPT-6 stub explicitly marked TBD — no invented API details
- [ ] Zero credentials/tokens/internal IDs in any output file
- [ ] `present_files` on the actual generated files
