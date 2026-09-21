#!/usr/bin/env python
import os
import sys
import warnings

## Suppress expected warnings before Django initialization
warnings.filterwarnings(
    "ignore", category=RuntimeWarning, message=".*received a naive datetime.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=".*Substituting font.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message='.*parameter "ln" is deprecated.*'
)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
