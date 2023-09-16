import re

from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_year(year):
    current_year = timezone.now().year
    if year > current_year:
        raise ValidationError(
            f'{year} не может быть больше {current_year}'
        )


def validate_username(username):
    if re.search(r'^[a-zA-Z][a-zA-Z0-9-_.]{1,150}$', username) is None:
        raise ValidationError(
            (f'Не допустимые символы <{username}> в нике.'),
        )