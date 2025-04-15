"""Модели для приложения users."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from backend.constants import (
    MAX_USER_EMAIL_LENGTH,
    MAX_USER_FIRST_NAME_LENGTH,
    MAX_USER_LAST_NAME_LENGTH,
    MAX_USER_USERNAME_LENGTH,
)


class User(AbstractUser):
    """Модель пользователя - основная сущность для аутентификации.

    Расширяет стандартную модель пользователя Django, добавляя поля для
    электронной почты, имени, фамилии и аватара. Обеспечивает уникальность
    email и username. Использует email в качестве основного поля для входа.
    """

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
        """Мета класс для пользователя.

        Определяет порядок сортировки по id, а также русскоязычные названия
        для единственного и множественного числа.
        """

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        """Строковое представление пользователя в формате 'Имя Фамилия'."""
        return f'{self.first_name} {self.last_name}'


class Follow(models.Model):
    """Модель для хранения подписок пользователей.

    Позволяет пользователям подписываться на других пользователей для
    получения обновлений о новых рецептах. Каждый пользователь может
    подписаться на другого пользователя только один раз. Запрещает
    подписку на самого себя.
    """

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
        """Мета класс для подписки.

        Определяет порядок сортировки по id, а также русскоязычные названия
        для единственного и множественного числа. Устанавливает ограничения
        на уникальность подписки и запрет подписки на самого себя.
        """

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
        """Строковое представление подписки."""
        return f'{self.follower} подписан на {self.followee}'
