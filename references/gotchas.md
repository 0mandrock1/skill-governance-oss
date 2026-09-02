# Gotchas

Environment-specific landmines. These are **not** rules — they are things that already went
wrong once. Cite the relevant entry from the workflow step that needs it, rather than copying
it into a skill body.

Each entry: symptom → cause → fix. Add entries as you burn yourself; delete them when the
underlying platform stops being broken.

---

## PDF generation with non-Latin text

**Symptom:** black boxes, blank glyphs, or mojibake where Cyrillic/Greek/CJK text should be.
**Cause:** the default PDF core fonts cover Latin-1 only.
**Fix:** register a Unicode TTF explicitly before use — e.g. with ReportLab,
`pdfmetrics.registerFont(TTFont("DejaVuSans", "<path>/DejaVuSans.ttf"))`, then set that font
family everywhere including table styles and headers. Bundle the TTF in the skill's `assets/`;
do not rely on a system font path existing.
**Also:** bold and italic are separate files. Registering only the regular face makes every
bold run silently fall back to a Latin-only font.

---

## Literal `\n` in note-app and API payloads

**Symptom:** a list arrives as one paragraph containing visible `\n`.
**Cause:** the payload was JSON-encoded twice, or the API treats the field as plain text.
**Fix:** send real newlines; for multi-item content, prefer one API call per block over one
call with embedded separators. Verify by reading the created document back, not by trusting
the success response.

---

## Publishing APIs and their client libraries

**Symptom:** an official-looking client library fails on auth, or silently mangles content.
**Cause:** many small publishing APIs have unmaintained third-party wrappers.
**Fix:** for small, stable, well-documented endpoints, call the HTTP API directly. Fewer
moving parts, and the failure mode is a readable status code.

---

## Randomness

**Symptom:** repeated draws correlate, or a "random" pick is challenged as unfair.
**Cause:** default PRNGs are deterministic and seeded predictably in short-lived runtimes.
**Fix:** for anything user-facing where fairness is contested (draws, giveaways, picking
between people), use a randomness service and record the result. For everything else — sampling,
shuffling examples, jitter — the standard library PRNG is correct and a network call is a
liability. **Always implement a local fallback with a logged warning**; a skill that hard-fails
offline because of a coin flip is a badly designed skill.

---

## Image hosting for embeds

**Symptom:** images render at publish time, then break days later.
**Cause:** CDN URLs from chat platforms and some editors are short-lived or scoped.
**Fix:** upload to a host you control or a durable image host, and embed that URL. Verify the
link resolves from a logged-out session before considering the publish complete.

---

## Serving files you already have on a web root

**Symptom:** a file is fetched over SSH/SFTP to be re-uploaded elsewhere.
**Cause:** habit.
**Fix:** if the path is already behind a web server, build the URL. Transferring bytes through
the agent to hand back a link is pure waste.

---

## Identifier flavours

**Symptom:** reads work, writes fail with a not-found error on an ID that visibly exists.
**Cause:** the platform distinguishes container IDs from data-source/collection IDs, and the
write path wants the other one.
**Fix:** record which flavour each registry row holds, and note it in the registry header.
Multi-source containers will reject the container ID outright; single-source ones accept both,
which is how this bug hides.

---

## Retired connectors

**Symptom:** a workflow half-works, writing to a system nobody reads any more.
**Cause:** the connector is still authenticated after the migration.
**Fix:** removal from the registry is the source of truth, not whether the connector still
responds. Availability is not permission.
