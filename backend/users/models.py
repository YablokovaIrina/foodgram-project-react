from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.settings import EMAIL_LENGHT, MAX_LENGHT_USER

from .validators import validate_username

ADMIN = 'admin'
USER = 'user'


class User(AbstractUser):
    ACCESS_LEVELS = (
        (ADMIN, 'Администратор'),
        (USER, 'Авторизованный пользователь'),
    )
    username = models.CharField(
        unique=True,
        max_length=MAX_LENGHT_USER,
        verbose_name='Логин',
        validators=(validate_username,),
    )
    first_name = models.CharField(
        max_length=MAX_LENGHT_USER,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGHT_USER,
        verbose_name='Фамилия пользователя',
    )
    password = models.CharField(
        max_length=MAX_LENGHT_USER,
        verbose_name='Пароль'
    )
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_LENGHT,
        verbose_name='Адрес электронной почты',
    )
    access_level = models.CharField(
        max_length=MAX_LENGHT_USER,
        choices=ACCESS_LEVELS,
        default=USER,
        verbose_name='Уровень доступа',
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return self.is_superuser or self.access_level == ADMIN

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'author'),
                                    name='unique follow'),
        ]
        ordering = ('user__username', 'author__username')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def str(self):
        return (
            f'{self.user.username} подписан на {self.author.username}'
        )
