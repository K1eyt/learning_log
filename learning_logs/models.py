"""Модели учебного журнала: тема и записи внутри неё."""
from django.conf import settings
from django.db import models
from django.urls import reverse


class TopicQuerySet(models.QuerySet):
    def owned_by(self, user):
        return self.filter(owner=user)

    def active(self):
        """Темы, которые не убраны в архив."""
        return self.filter(is_archived=False)

    def with_counters(self):
        """Добавляет число записей и дату последней записи."""
        return self.annotate(
            entries_total=models.Count('entries'),
            entries_last=models.Max('entries__date_added'),
        )


class Topic(models.Model):
    """Тема, которую изучает пользователь."""

    text = models.CharField('название темы', max_length=200)
    date_added = models.DateTimeField('создана', auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='topics', verbose_name='владелец')
    is_favorite = models.BooleanField('в избранном', default=False)
    is_archived = models.BooleanField(
        'в архиве', default=False,
        help_text='Архивные темы не показываются в основном списке, но не удаляются.',
    )

    objects = TopicQuerySet.as_manager()

    class Meta:
        ordering = ['-is_favorite', 'text']
        verbose_name = 'тема'
        verbose_name_plural = 'темы'
        constraints = [
            models.UniqueConstraint(fields=['owner', 'text'], name='unique_topic_per_owner'),
        ]

    def __str__(self):
        """Возвращает строковое представление модели."""
        return self.text

    def get_absolute_url(self):
        return reverse('learning_logs:topic', args=[self.pk])


class Entry(models.Model):
    """Запись о том, что изучено по теме."""

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='entries',
                              verbose_name='тема')
    text = models.TextField('текст записи')
    date_added = models.DateTimeField('добавлена', auto_now_add=True)
    date_modified = models.DateTimeField('изменена', auto_now=True)

    class Meta:
        ordering = ['-date_added']
        verbose_name = 'запись'
        verbose_name_plural = 'entries'

    def __str__(self):
        """Первые 50 символов записи."""
        return self.text if len(self.text) <= 50 else f'{self.text[:50]}...'

    @property
    def is_edited(self):
        """Запись считается исправленной, если её меняли позже минуты после создания."""
        return (self.date_modified - self.date_added).total_seconds() > 60
