---
name: user-skill-router
description: Route requests to detailed user-scope skills without injecting every description. Use for Apple apps, Riela, browser automation, diagrams, Git safety, security, Product Hunt, Wrike, Swift/iOS, invoices, environment setup, or an explicitly named user skill.
---

# User Skill Router

Load one detailed user skill only when the request needs it.

## Routing

Map the request to the narrowest matching skill:

- Apple Calendar, Mail, Notes, Reminders, notifications, alarms, or cross-domain
  Apple access: `apple-calendar`, `apple-schedule`, `apple-mail`, `apple-notes`,
  `apple-reminders`, `apple-notifications`, `apple-clock-alarms`, or
  `apple-gateway`
- Riela packages, workflows, execution, testing, troubleshooting, or explicit
  `/riela` requests: `riela` first; let its routing select a narrower Riela skill
- Browser UI operation: `brave-browser-computer-use`
- Diagrams: `diagram-design`
- Pre-commit safety or GitHub Actions: `git-precommit-safety-check` or
  `secure-github-action`
- Source security review: `codex-source-security-check-loop`
- Session self-review: `improve`
- Environment setup: `envrc-generate`
- Product Hunt, Wrike, invoice/PDF correction, Swift, iOS app launch, Konjac,
  Miro, task queue, or task watchdog work: use the same-named installed skill

If the user explicitly names a user skill, prefer that exact name.

## Loading

1. Look for the selected skill at `~/.agents/skills/<name>/SKILL.md`, then at
   `~/.codex/skills/<name>/SKILL.md`.
2. Read the selected `SKILL.md` completely before acting.
3. Follow its instructions as though it had triggered directly.
4. If neither path exists, state that the requested user skill is unavailable
   and continue with the safest applicable fallback.

Do not scan or load every installed skill. Load only the selected skill.
