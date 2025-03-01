from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.constants import MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        blank=False, null=False, unique=True, max_length=MAX_LENGTH
    )
    avatar = models.ImageField()
    subscriptions = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='subscribers',
        blank=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_admin(self):
        """Возвращает True, если пользователь админ."""
        return self.is_superuser and self.is_staff

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
