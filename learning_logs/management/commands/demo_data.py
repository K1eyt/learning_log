"""
Наполняет пустой сайт данными для демонстрации.

Создаёт двух пользователей с паролем из DEMO_PASSWORD и несколько тем с
записями, чтобы проверяющий сразу видел рабочий сайт и мог убедиться, что
чужие темы недоступны. Повторный запуск ничего не дублирует, без
DEMO_PASSWORD команда не делает ничего.
"""
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from learning_logs.models import Topic

# (название темы, избранное, в архиве, [записи])
DEMO = {
    'dmitry': [
        ('Django', True, False, [
            'Проект создаётся командой django-admin startproject, приложение - python manage.py startapp.',
            'После правки моделей нужны две команды: makemigrations готовит миграцию, migrate применяет её.',
            'Чтобы чужая тема не открывалась, объект берут сразу с условием по владельцу: '
            'get_object_or_404(Topic, pk=topic_id, owner=request.user). Тогда ответ будет 404.',
        ]),
        ('Английский', False, False, [
            'Present Perfect: have или has плюс третья форма глагола. I have already finished.',
            'Слово дня: thorough - тщательный, основательный.',
        ]),
        ('Старый конспект', False, True, [
            'Эта тема убрана в архив: она не мешает в списке, но сохранилась.',
        ]),
    ],
    'olga': [
        ('Акварель', True, False, [
            'Сначала светлые слои, тёмные - в конце. Исправлять белым в акварели нечем.',
            'Бумага плотностью от 200 г/м2 не так сильно коробится от воды.',
        ]),
        ('Личные заметки', False, False, [
            'Эту тему видит только olga: у dmitry она не откроется даже по прямой ссылке.',
        ]),
    ],
}


class Command(BaseCommand):
    help = 'Создать демонстрационных пользователей dmitry и olga с темами и записями.'

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD', '')
        if not password:
            self.stdout.write('demo_data: DEMO_PASSWORD не задан, пропускаю.')
            return

        for username, topics in DEMO.items():
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            if Topic.objects.filter(owner=user).exists():
                continue

            for text, favorite, archived, entries in topics:
                topic = Topic.objects.create(owner=user, text=text, is_favorite=favorite,
                                             is_archived=archived)
                for entry_text in entries:
                    topic.entries.create(text=entry_text)
            self.stdout.write(f'demo_data: данные для {username} созданы.')
