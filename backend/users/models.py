from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator

from backend.constants import (
    MAX_USER_FIRST_NAME_LENGTH, MAX_USER_LAST_NAME_LENGTH,
    MAX_USER_EMAIL_LENGTH, MAX_USER_USERNAME_LENGTH)


class User(AbstractUser):
    first_name = models.CharField(
        max_length=MAX_USER_FIRST_NAME_LENGTH,
        verbose_name='Имя',
        help_text='Имя пользователя'
    )
    last_name = models.CharField(
        max_length=MAX_USER_LAST_NAME_LENGTH,
        verbose_name='Фамилия',
        help_text='Фамилия пользователя'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар',
        help_text='Аватар пользователя'
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_USER_EMAIL_LENGTH,
        verbose_name='Email',
        help_text='Email пользователя'
    )
    username = models.CharField(
        unique=True,
        max_length=MAX_USER_USERNAME_LENGTH,
        verbose_name='Имя пользователя',
        validators=[UnicodeUsernameValidator()]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик'
    )
    followee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followee'], name='unique_follow'),
            models.CheckConstraint(
                check=~models.Q(follower=models.F('followee')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.follower} подписан на {self.followee}'
