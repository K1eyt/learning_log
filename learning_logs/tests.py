"""Тесты учебного журнала: доступ, владельцы, формы, избранное, архив, экспорт."""
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .models import Entry, Topic


class JournalTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dmitry = User.objects.create_user('dmitry', password='pass-12345')
        cls.olga = User.objects.create_user('olga', password='pass-12345')
        cls.topic = Topic.objects.create(owner=cls.dmitry, text='Django')
        cls.entry = Entry.objects.create(topic=cls.topic, text='Первая запись')
        cls.foreign = Topic.objects.create(owner=cls.olga, text='Акварель')

    def link(self, name, *args):
        return reverse(f'learning_logs:{name}', args=args)


class AccessTests(JournalTestCase):
    def test_home_is_open_for_guest(self):
        response = self.client.get(self.link('index'))
        self.assertContains(response, 'Регистрация')

    def test_home_shows_counters_for_owner(self):
        self.client.force_login(self.dmitry)
        response = self.client.get(self.link('index'))
        self.assertEqual(response.context['total_topics'], 1)
        self.assertEqual(response.context['total_entries'], 1)

    def test_pages_require_login(self):
        pages = [
            self.link('topics'), self.link('new_topic'),
            self.link('topic', self.topic.pk), self.link('new_entry', self.topic.pk),
            self.link('edit_entry', self.entry.pk), self.link('rename_topic', self.topic.pk),
            self.link('delete_topic', self.topic.pk), self.link('export_topic', self.topic.pk),
        ]
        for url in pages:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), f"{reverse('users:login')}?next={url}")

    def test_healthz_does_not_need_login(self):
        self.assertEqual(self.client.get('/healthz/').content, b'ok')

    def test_missing_page_is_404(self):
        self.assertEqual(self.client.get('/no-such-page/').status_code, 404)


class OwnerTests(JournalTestCase):
    def setUp(self):
        self.client.force_login(self.dmitry)

    def test_list_shows_only_own_topics(self):
        response = self.client.get(self.link('topics'))
        self.assertContains(response, 'Django')
        self.assertNotContains(response, 'Акварель')

    def test_foreign_topic_is_404_everywhere(self):
        pages = [
            ('get', self.link('topic', self.foreign.pk)),
            ('get', self.link('rename_topic', self.foreign.pk)),
            ('get', self.link('export_topic', self.foreign.pk)),
            ('get', self.link('delete_topic', self.foreign.pk)),
            ('post', self.link('delete_topic', self.foreign.pk)),
            ('post', self.link('toggle_favorite', self.foreign.pk)),
            ('post', self.link('toggle_archive', self.foreign.pk)),
            ('post', self.link('new_entry', self.foreign.pk)),
        ]
        for method, url in pages:
            with self.subTest(url=url, method=method):
                response = getattr(self.client, method)(url, {'text': 'взлом'})
                self.assertEqual(response.status_code, 404)

        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.text, 'Акварель')
        self.assertFalse(self.foreign.is_favorite)
        self.assertEqual(self.foreign.entries.count(), 0)

    def test_foreign_entry_cannot_be_changed(self):
        foreign_entry = Entry.objects.create(topic=self.foreign, text='Чужая запись')
        url = self.link('edit_entry', foreign_entry.pk)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'text': 'взлом'}).status_code, 404)
        self.assertEqual(self.client.post(self.link('delete_entry', foreign_entry.pk)).status_code, 404)
        foreign_entry.refresh_from_db()
        self.assertEqual(foreign_entry.text, 'Чужая запись')

    def test_missing_id_is_404(self):
        for name in ('topic', 'rename_topic', 'delete_topic', 'new_entry', 'export_topic'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.link(name, 99999)).status_code, 404)
        self.assertEqual(self.client.get(self.link('edit_entry', 99999)).status_code, 404)


class PagesOpenTests(JournalTestCase):
    """Каждая страница владельца открывается обычным переходом по ссылке."""

    def setUp(self):
        self.client.force_login(self.dmitry)

    def test_all_owner_pages_render(self):
        pages = [
            self.link('index'), self.link('topics'), self.link('topic', self.topic.pk),
            self.link('new_topic'), self.link('rename_topic', self.topic.pk),
            self.link('delete_topic', self.topic.pk), self.link('new_entry', self.topic.pk),
            self.link('edit_entry', self.entry.pk), self.link('delete_entry', self.entry.pk),
            self.link('export_topic', self.topic.pk),
            reverse('users:profile'), reverse('users:password_change'),
        ]
        for url in pages:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class TopicFormTests(JournalTestCase):
    def setUp(self):
        self.client.force_login(self.olga)

    def test_new_topic_belongs_to_current_user(self):
        response = self.client.post(self.link('new_topic'), {'text': 'Гитара', 'owner': self.dmitry.pk})
        created = Topic.objects.get(text='Гитара')
        self.assertEqual(created.owner, self.olga)
        self.assertRedirects(response, self.link('topic', created.pk))

    def test_duplicate_topic_is_rejected(self):
        response = self.client.post(self.link('new_topic'), {'text': 'акварель'})
        self.assertIn('text', response.context['form'].errors)
        self.assertEqual(Topic.objects.filter(owner=self.olga).count(), 1)

    def test_same_name_allowed_for_different_users(self):
        self.client.post(self.link('new_topic'), {'text': 'Django'})
        self.assertEqual(Topic.objects.filter(text='Django').count(), 2)

    def test_empty_topic_shows_error(self):
        response = self.client.post(self.link('new_topic'), {'text': ''})
        self.assertIn('text', response.context['form'].errors)

    def test_rename_topic(self):
        self.client.post(self.link('rename_topic', self.foreign.pk), {'text': 'Акварель и тушь'})
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.text, 'Акварель и тушь')


class EntryTests(JournalTestCase):
    def setUp(self):
        self.client.force_login(self.dmitry)

    def test_add_entry(self):
        self.client.post(self.link('new_entry', self.topic.pk), {'text': 'Вторая запись'})
        self.assertEqual(self.topic.entries.count(), 2)

    def test_edit_entry(self):
        self.client.post(self.link('edit_entry', self.entry.pk), {'text': 'Исправленная'})
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.text, 'Исправленная')

    def test_delete_entry_needs_post(self):
        response = self.client.get(self.link('delete_entry', self.entry.pk))
        self.assertContains(response, 'Да, удалить')
        self.assertTrue(Entry.objects.filter(pk=self.entry.pk).exists())

        self.client.post(self.link('delete_entry', self.entry.pk))
        self.assertFalse(Entry.objects.filter(pk=self.entry.pk).exists())

    def test_delete_topic_removes_entries(self):
        self.client.post(self.link('delete_topic', self.topic.pk))
        self.assertFalse(Topic.objects.filter(pk=self.topic.pk).exists())
        self.assertFalse(Entry.objects.filter(pk=self.entry.pk).exists())

    def test_entries_are_newest_first(self):
        second = Entry.objects.create(topic=self.topic, text='Вторая')
        response = self.client.get(self.link('topic', self.topic.pk))
        self.assertEqual([e.pk for e in response.context['entries']], [second.pk, self.entry.pk])


class ExtraFeatureTests(JournalTestCase):
    def setUp(self):
        self.client.force_login(self.dmitry)

    def test_favorite_toggles_back_and_forth(self):
        self.client.post(self.link('toggle_favorite', self.topic.pk))
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.is_favorite)

        self.client.post(self.link('toggle_favorite', self.topic.pk))
        self.topic.refresh_from_db()
        self.assertFalse(self.topic.is_favorite)

    def test_favorite_by_get_is_rejected(self):
        self.assertEqual(self.client.get(self.link('toggle_favorite', self.topic.pk)).status_code, 405)

    def test_archive_hides_topic_from_main_list(self):
        self.client.post(self.link('toggle_archive', self.topic.pk))
        # Название темы встречается и в подвале сайта, поэтому сверяем сам список.
        active = self.client.get(self.link('topics'))
        archive = self.client.get(self.link('topics'), {'archived': '1'})
        self.assertEqual(list(active.context['topics']), [])
        self.assertEqual([t.pk for t in archive.context['topics']], [self.topic.pk])
        self.assertEqual(active.context['counts'], {'active': 0, 'archived': 1})

    def test_archiving_clears_favorite(self):
        self.client.post(self.link('toggle_favorite', self.topic.pk))
        self.client.post(self.link('toggle_archive', self.topic.pk))
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.is_archived)
        self.assertFalse(self.topic.is_favorite)

    def test_search_finds_by_entry_text_in_any_case(self):
        response = self.client.get(self.link('topics'), {'q': 'ПЕРВАЯ'})
        self.assertEqual([t.pk for t in response.context['topics']], [self.topic.pk])

    def test_search_without_matches(self):
        response = self.client.get(self.link('topics'), {'q': 'ничего такого'})
        self.assertEqual(len(response.context['topics']), 0)

    def test_export_returns_markdown_file(self):
        response = self.client.get(self.link('export_topic', self.topic.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        body = response.content.decode()
        self.assertIn('# Django', body)
        self.assertIn('Первая запись', body)


class OwnerMigrationTests(TransactionTestCase):
    """Темы, созданные до появления владельца, получают существующего пользователя."""

    before = [('learning_logs', '0001_initial')]
    after = [('learning_logs', '0002_topic_owner')]
    auth = [('auth', '0012_alter_user_first_name_max_length')]

    def test_existing_topics_get_owner(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old_apps = executor.loader.project_state(self.before + self.auth).apps
        admin = old_apps.get_model('auth', 'User').objects.create(username='admin', is_superuser=True)
        old_apps.get_model('learning_logs', 'Topic').objects.create(text='Старая тема')

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.after)
        new_apps = executor.loader.project_state(self.after).apps
        migrated = new_apps.get_model('learning_logs', 'Topic').objects.get(text='Старая тема')
        self.assertEqual(migrated.owner_id, admin.pk)

        # Возвращаем схему в актуальное состояние для остальных тестов.
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
