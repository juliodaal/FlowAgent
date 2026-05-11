# Security Policy

## Reporting a vulnerability

If you discover a security issue, please **do not** open a public GitHub issue.

Instead, email **juliocesar.daal@gmail.com** with:

- A description of the issue and its potential impact
- Steps to reproduce
- Any suggested mitigation

You can expect an initial acknowledgement within 72 hours. Coordinated
disclosure is appreciated — please give a reasonable window before publishing
details so a fix can be released.

## Secrets policy for this repository

This project is public. The following rules apply to **every** contribution:

1. **Never commit secrets.** API keys, tokens, passwords, private keys, IMAP
   credentials, OAuth client secrets — none of them belong in the repository.
2. All configuration that can vary between environments lives in `.env` files,
   which are git-ignored. A safe template is provided as `.env.example` with
   placeholder values only.
3. CI runs [`gitleaks`](https://github.com/gitleaks/gitleaks) on every push
   and pull request. PRs that introduce secret-like patterns will fail.
4. A `pre-commit` hook with `gitleaks` is configured locally — install it
   with `pre-commit install` after cloning so leaks are caught before the
   commit lands.
5. If a secret is leaked accidentally, **rotate it immediately** at the
   provider (OpenAI, Notion, Supabase, etc.) and force-push a history rewrite
   only after coordinating with the maintainer. Rotation comes first; the git
   history fix is secondary.

## Supported versions

Only the `main` branch is supported. Tagged releases are snapshots intended
for portfolio/demo purposes and do not receive backports.

## Threat model (summary)

FlowAgent is intended to be **run locally or in a single-user environment**.
It is not hardened for multi-tenant deployment. In particular:

- The FastAPI auth token guards local-only access; rotate it if you expose the
  service to the public internet (and add a real auth layer first).
- n8n is exposed on localhost by default; do not bind it to a public interface
  without a reverse proxy + auth.
- The agent has tools that read email and write to Notion — treat the OpenAI
  key and tool credentials as if a successful prompt injection could exfiltrate
  data through those tools. Review tool outputs before trusting them.
