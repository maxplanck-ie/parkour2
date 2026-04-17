---
applyTo: "**/*.vue,**/*.ts,**/*.js"
---

# Vue 3 / Vite / TypeScript / JavaScript

- Use Vue 3 Composition API; be consistent with existing patterns in the repo.
- Keep components focused; extract shared logic into composables or utilities only when it clearly reduces duplication.
- Use the project's existing API client/wrappers; do not introduce new networking patterns.
- Keep state changes predictable: do not mutate props; follow established store patterns.
- Rebuild the frontend with `npm run build`.
