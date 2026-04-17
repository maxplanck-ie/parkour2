# Copilot Chat Instructions

These instructions apply to **Copilot Chat** in VS Code for this repository.
Path-specific rules live in `.github/instructions/` and are applied automatically
based on the file you are editing (see [GitHub docs](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)).

## Principles

- **KISS**: prefer the simplest solution that meets the requirements.
- Prefer small, focused changes; avoid speculative refactors.
- Do not introduce new dependencies unless explicitly requested.
- If requirements or existing patterns are unclear, ask up to 3 clarifying questions instead of guessing.

## Architecture

- **Backend**: Django + Django REST Framework (DRF).
- **Frontend**: Vue 3 with Vite.
- Reuse existing utilities and components before creating new ones.
- Keep business logic out of views (backend) and out of UI components (frontend).

## Commands

- Run backend tests: `python manage.py test --parallel`
- Build frontend: `npm run build`

## Security

- Never log secrets or sensitive data.
- Validate and sanitize all user input.
- Use Django ORM; avoid raw SQL unless strictly necessary.
- Follow least-privilege and safe-default patterns.
