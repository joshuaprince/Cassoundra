import os

from django.db import models
from .validators import validate_extension, validate_size


def upl_to(instance, fn):
    return os.path.join('sound', instance.name + '.mp3')


class Sound(models.Model):
    name = models.CharField(max_length=32, default='', unique=True)
    file = models.FileField(
        upload_to=upl_to,
        validators=[validate_extension, validate_size]
    )
    play_count = models.IntegerField(default=0)
    loud = models.BooleanField(default=False)

    def __str__(self):
        return self.name
