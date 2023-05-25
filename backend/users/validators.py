import re

from django.core.exceptions import ValidationError
from foodgram.settings import FORBIDDEN_NAME


def validate_username(value):
    if value == FORBIDDEN_NAME:
        raise ValidationError(
            'Имя пользователя {FORBIDDEN_NAME} не разрешено.'
        )
    forbidden_symbols = "".join(set(re.sub(r"[\w.@+-]+", "", value)))
    if forbidden_symbols:
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы:'
            f'{forbidden_symbols}'
        )
    return value
