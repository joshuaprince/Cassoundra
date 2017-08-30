
from django.core.exceptions import ValidationError


def validate_extension(value):
    if not value.name.endswith('.mp3'):
        raise ValidationError(u'Bad file extension')  # todo


def validate_size(value):
    limit = 1 * 1024 * 1024  # 1MB
    if value.size > limit:
        raise ValidationError(u'File is too large. 1MB maximum')  # todo


def validate_name(value):
    if not value.isalnum():
        raise ValidationError(u'Command must consist of only letters and numbers.')
