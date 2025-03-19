from django.db import models

from backend.constants import (
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH
)


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=MAX_TAG_NAME_LENGTH)
    slug = models.SlugField(unique=True, max_length=MAX_TAG_SLUG_LENGTH)

    def __str__(self):
        return self.name
