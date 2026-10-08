# Webbie local action gateway

This source batch is stacked on the native workspace-launcher branch. It introduces a shared action registry and local approval queue, without replacing the installed voice agent, speaker enrollment, memory or service files.

## Implemented registry

| Action | Level | Behavior |
| --- | --- | --- |
| `system.health` | 1 | Read-only Guardian report |
| `workspace.open` | 1 | Fixed registered native workspace entry point |
| `vault.snapshot` | 2 | Local verified snapshot after request-specific approval; never uploads |
| `service.restart` | 3 | Restart Webbie or AI DJ user service after explicit request-specific confirmation, then check active state |

Unknown actions, extra parameters, arbitrary command strings, privileged host service changes and destructive operations are rejected. Service activity still does not prove authorized conversation, playback or broadcasting.

Workspace modes: Normal, School Tutor, Author Editor, Studio Producer, AI DJ, Researcher, Developer, System Technician and Security Assistant. `school` and `study` preserve the existing Study launch path. Mode guidance is available as context to a future assistant adapter; it does not change the live agent's system prompt by itself.

## Local CLI

Use `webbie/actions/webbie-action` from a checkout or `/usr/local/lib/spider-os/webbie/actions/webbie-action` on a selected-module deployment:

```bash
webbie-action mode
webbie-action request system.health
webbie-action request workspace.open --params '{"workspace":"studio"}'
webbie-action request vault.snapshot
webbie-action pending
```

A Level 2/3 request returns an opaque request ID and the exact action/parameters awaiting approval. After reviewing that request, the local user-facing control can approve it:

```bash
webbie-action approve REQUEST_ID --confirm-action vault.snapshot
webbie-action deny REQUEST_ID
```

For an explicitly desired service restart, request it first, inspect `pending`, then approve the returned ID with `--confirm-action service.restart`. Approval is stored separately from the request, applies only to the recorded parameters, expires after five minutes and cannot be replayed. Failed execution consumes the approval and reports failure rather than success. Interrupted `running` actions are not retried automatically, because their side effects may already have occurred.

The state directory is `~/.local/state/spider-os/action-gateway` with mode 0700, and the request database is mode 0600. Approval state survives process restarts. Audit records contain action metadata and parameters, not journal contents, microphone recordings, exception details or assistant conversations. Private filenames are not part of the current action parameter schema. There is no automatic log-retention cleanup yet.

## Trust boundary and remaining integration

This is a same-user local CLI/Python API, not an HTTP endpoint or sandbox against other programs already running as the owner. Only trusted user-facing code may call `approve`; do not expose approval as an unrestricted language-model tool. A local program with the owner's filesystem privileges can change local state, so these records do not defend against a compromised user account.

Voice and network adapter requests are rejected. The later voice adapter must authenticate the enrolled speaker before submitting any request, independently of names spoken in text. Speaker verification must remain mandatory; an asserted name, model-generated field or recognized wake phrase is not authorization. Default intended voice users remain the validated owner and explicitly enrolled second trusted user. This batch does not alter that live gate or enroll anyone.

Before connecting the assistant, implement and qualify a visible local approval surface, authenticated caller/session handling, voice-to-request binding and real multi-turn/microphone tests on the installed machine. Do not make the language model the approver. Project edits, manuscript saves, uploads, browser form submissions, package installation, boot repair and security-policy changes are not implemented actions.

The API reports `launch_requested` for app launches, rather than claiming the application reached a working state. Missing workspace modules fail clearly. The gateway is packaged as part of the existing Webbie directory, and no service/autostart is added. Installed-machine checklist gates remain unchecked.

## Validation

Regression coverage includes low-risk actions, request-specific approval, action mismatch, expiry, denial, replay after reopening the queue, wrong-owner records, symlink rejection, unknown actions/extra parameters, voice/network rejection, private failure-message handling, local-only snapshots and exact fixed service restart commands with post-restart state checks. Existing recovery/launcher tests and the GitHub desktop smoke test remain required.
