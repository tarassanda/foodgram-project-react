import re

from django.core.exceptions import ValidationError


def validate_username(username):
    if username == 'me':
        raise ValidationError(
            ('Имя пользователя не может быть <me>.'),
        )
    if re.search(r'^[a-zA-Z][a-zA-Z0-9-_.]{1,150}$', username) is None:
        raise ValidationError(
            (f'Недопустимые символы <{username}> в нике.'),
        )
