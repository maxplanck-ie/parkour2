import warnings


def pytest_configure(config):
    """Suppress warnings that are expected during Django test runs.

    1. RuntimeWarning: naive datetime when USE_TZ is True (test fixtures
       intentionally use naive datetimes for deterministic test data).
    2. DeprecationWarning: fpdf2 font substitution (Arial -> Helvetica).
    3. DeprecationWarning: fpdf2 deprecated `ln` cell parameter.
    """
    config.addinivalue_line("markers", "django: mark test as django test")

    warnings.filterwarnings(
        "ignore",
        message=".*DateTimeField.*received a naive datetime.*",
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Substituting font.*",
    )
    warnings.filterwarnings(
        "ignore",
        message='.*parameter "ln" is deprecated.*',
    )
