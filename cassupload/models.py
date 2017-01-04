import os

from django.db import models
from .validators import validate_extension, validate_size


def upl_to(instance, fn):
    return os.path.join('sound', instance.name + '.mp3')


class Guild(models.Model):
    snowflake = models.CharField(max_length=64)

    def __str__(self):
        return self.snowflake


class Sound(models.Model):
    name = models.CharField(max_length=32, default='', unique=True)
    file = models.FileField(
        upload_to=upl_to,
        validators=[validate_extension, validate_size]
    )
    play_count = models.IntegerField(default=0)  # TODO this doesn't do anything yet

    def __str__(self):
        return self.name