# State Registry — this repository's own shipped skills (example, not a template)

This is a small, filled example of `state-registry.template.md` in use — registering the one
piece of state any skill in this repository actually owns. It is safe to ship: no
infrastructure IDs, no credentials, no hostnames. Compare it against your own private,
git-ignored registry when you write one; do not confuse the two.

## Filesystem / CDN state

| Location | Owner skill | Public ops | Public URL pattern | Verified |
|---|---|---|---|---|
| `{RUNS}` run-log directory (path set by the instance, default `$CC_RUNS`) | cc-remote-agent | `cc_remote_agent.spawn/poll/result/cancel/chain` | n/a — local filesystem, not published | 2026-09-02 |
