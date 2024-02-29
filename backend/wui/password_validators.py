from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Stolen from https://stackoverflow.com/questions/67155953/django-auth-password-validators-check-for-symbols-and-other-requirements

class CapitalSymbolPasswordValidator:
    def __init__(self, number_capitals=2, number_symbols=2, symbols="[~!@#$%^&*()_+{}\":;'[]"):
        self.number_capitals = number_capitals
        self.number_symbols = number_symbols
        self.symbols = symbols

    def validate(self, password, user=None):
        capitals = [char for char in password if char.isupper()]
        symbols = [char for char in password if char in self.symbols]
        if len(capitals) < self.number_capitals:
            raise ValidationError(
                _("This password must contain at least %(min_length)d capital letters."),
                code='password_too_short',
                params={'min_length': self.number_capitals},
            )
        if len(symbols) < self.number_symbols:
            raise ValidationError(
                _("This password must contain at least %(min_length)d symbols."),
                code='password_too_short',
                params={'min_length': self.number_symbols},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(number_capitals)d capital letters and %(number_symbols)d symbols."
            % {'number_capitals': self.number_capitals, 'number_symbols': self.number_symbols}
        )