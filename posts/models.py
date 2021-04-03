import textwrap

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """A group section model for grouping user posts.
    So far, the group is created by the administrator.
    """

    title = models.CharField(
        verbose_name='Название',
        max_length=200,
        help_text='ГранЪесловникЪ для группы дать',
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=200,
        unique=True,
        blank=True,
        help_text='Задать руками иЛЪ оставить машинамЪ шансЪ',
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Группы описания',
    )

    def __str__(self):
        return textwrap.shorten(self.title, 15)


class Post(models.Model):
    """Specified model by conditions.
    The main site model.
    """

    text = models.TextField(
        verbose_name='Тело поста',
        help_text='Наполнить пост',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        help_text='Выбор группы не обязателен, '
                  'но желателен',
    )
    image = models.ImageField(
        upload_to='posts/', blank=True, null=True
    )

    def __str__(self):
        return textwrap.shorten(self.text, 15)


class Comment(models.Model):
    """The comment model is tied to the post, many to one,
    by the author, by the date. deletion cascade.
    """

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField()
    created = models.DateTimeField(
        auto_now_add=True,
    )


class Follow(models.Model):
    """A model for subscribing to authors,
    and handling user subscriptions.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )


class Meta:
    ordering = ('-pub_date',)
