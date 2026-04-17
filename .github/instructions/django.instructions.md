---
applyTo: "**/*.py"
---

# Python / Django / DRF

- Use DRF serializers for input validation and response shaping.
- Keep business logic out of views; place it in service modules or helpers consistent with the existing codebase.
- Use the Django ORM; avoid raw SQL unless necessary and clearly justified.
- Follow existing naming, module, and package conventions in the repo.
- Add or adjust tests for behaviour changes; run with `python manage.py test --parallel`.
- Use type hints where they improve clarity; avoid overly generic abstractions.
