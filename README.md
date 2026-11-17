# Learning Log - учебный журнал

[![tests](https://github.com/Makson61/learning-log/actions/workflows/ci.yml/badge.svg)](https://github.com/Makson61/learning-log/actions/workflows/ci.yml)

Личный журнал того, что вы изучаете: темы и записи к ним. Записи видит только их владелец.

**Рабочий сайт:** https://makson-learning-log.onrender.com

Учебный проект на Django 5.2 LTS (РКСИ, курс «Python и Django»).

## Как проверить

На сайте уже есть данные и два пользователя, чтобы сразу увидеть разграничение доступа:

| Кто | Логин | Пароль |
|---|---|---|
| Пользователь 1 | `dmitry` | передан вместе со ссылкой |
| Пользователь 2 | `olga` | передан вместе со ссылкой |
| Администратор (`/admin/`) | `review_admin` | передан вместе со ссылкой |

Можно зарегистрировать и своего пользователя. Проверка разграничения: войдите под `dmitry`,
запомните адрес любого его объекта, затем войдите под `olga` и откройте тот же адрес - будет 404.

## Что умеет

Обязательная часть задания:

- Темы и записи к ним, страницы создания и редактирования - как в учебнике.
- Регистрация с автоматическим входом, вход, выход **только POST-формой** с CSRF-токеном.
- Тема принадлежит пользователю: чужая тема и чужая запись не открываются даже по прямой ссылке (ответ 404).
- Владелец темы добавлен отдельной миграцией: старые темы получают существующего пользователя, `default=1` в модели нет.
- Оформление на Bootstrap 4 через `django-bootstrap4`, рабочий вид на телефоне.

Сверх задания:

- **Избранное**: тема со звёздочкой поднимается в начало списка и попадает на главную.
- **Архив**: отработанная тема убирается из списка, но не удаляется; из архива её можно вернуть.
- **Экспорт темы** в текстовый файл Markdown - все записи от старых к новым одним файлом.
- Поиск по названиям тем и тексту записей, без учёта регистра и для русского текста тоже.
- Переименование темы, удаление темы и записи с отдельной страницей подтверждения.
- Одинаковые названия тем у одного пользователя не допускаются, у разных - пожалуйста.
- Постраничный вывод записей, отметка «исправлена» у изменённых записей.
- Сводка на главной, профиль пользователя, смена пароля, свои страницы 404 и 500.

## Страницы

| Страница | Адрес | Кому доступна |
|---|---|---|
| Главная | `/` | всем |
| Мои темы, поиск, архив | `/topics/` | после входа |
| Тема с записями | `/topics/<id>/` | только владельцу |
| Новая тема | `/new_topic/` | после входа |
| Переименовать, удалить тему | `/topics/<id>/rename/`, `/topics/<id>/delete/` | только владельцу |
| Избранное, архив | `/topics/<id>/favorite/`, `/topics/<id>/archive/` (POST) | только владельцу |
| Скачать тему | `/topics/<id>/export/` | только владельцу |
| Новая запись | `/new_entry/<topic_id>/` | только владельцу темы |
| Изменить, удалить запись | `/edit_entry/<id>/`, `/entries/<id>/delete/` | только владельцу |
| Вход, регистрация, выход | `/users/login/`, `/users/register/`, `/users/logout/` (POST) | всем |

## Разграничение доступа

Объект для изменения всегда достаётся вместе с условием по владельцу:

```python
topic = get_object_or_404(Topic, pk=topic_id, owner=request.user)
entry = get_object_or_404(Entry, pk=entry_id, topic__owner=request.user)
```

Поэтому чужой и несуществующий номер дают один и тот же ответ 404, и по ответу нельзя узнать,
существует ли чужая тема. Скрытая в шаблоне ссылка - это удобство, а не защита: адрес можно набрать руками.

## Как это устроено внутри

| Файл или каталог | Зачем |
|---|---|
| `learning_log/settings.py` | Настройки. Всё, что зависит от сервера, читается из переменных окружения |
| `learning_log/env.py` | Разбор переменных окружения: строки, числа, списки, флаги |
| `learning_logs/models.py` | Тема и запись, избранное и архив |
| `learning_logs/views.py` | Функции представления: список тем, тема, формы, экспорт |
| `learning_logs/lookups.py` | Поиск без учёта регистра для кириллицы в SQLite |
| `learning_logs/management/commands/demo_data.py` | Демонстрационные данные одной командой |
| `users/` | Регистрация, вход, выход POST-запросом, профиль, смена пароля |
| `users/management/commands/ensure_admin.py` | Администратор из переменных окружения |
| `users/management/commands/prestart.py` | Миграции, администратор и демо-данные за один запуск |
| `templates/base.html` | Общий шаблон: тёмная шапка Bootstrap 4, меню, сообщения |
| `static/css/app.css` | Оформление поверх Bootstrap |
| `Dockerfile`, `compose.yaml`, `start.sh` | Запуск в контейнере |
| `render.yaml` | Описание бесплатного сервиса на Render |

## Запуск на своём компьютере

```sh
git clone https://github.com/Makson61/learning-log.git
cd learning-log
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # Linux или macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Откроется http://127.0.0.1:8000/. Без файла `.env` проект работает в режиме разработки:
`DEBUG=True`, база SQLite рядом с `manage.py`.

Демонстрационные данные для проверки:

```sh
DEMO_PASSWORD=любой-пароль python manage.py demo_data
```

## Проверка

```sh
python manage.py check
python manage.py test
```

Тесты проверяют:

- личные страницы требуют входа, гость уходит на страницу входа;
- в списке только свои темы, чужая тема и запись дают 404 и не меняются;
- новая тема получает текущего владельца, поле `owner` из запроса игнорируется;
- повторное название темы у одного пользователя отклоняется, у разного - нет;
- несуществующий номер даёт 404, удаление запросом GET только показывает подтверждение;
- избранное и архив переключаются только POST-запросом, архив снимает избранное;
- поиск находит по тексту записи и не зависит от регистра;
- экспорт отдаёт файл с заголовком темы и текстом записей;
- миграция владельца назначает старым темам существующего пользователя;
- регистрация, вход, выход только POST-запросом с CSRF-токеном, профиль;
- команды `ensure_admin`, `demo_data` и `prestart`.

## Развёртывание на сервере через Docker Compose

Нужен сервер с Docker и плагином Compose и домен, направленный на этот сервер.

1. Получите код и создайте `.env`:

   ```sh
   git clone https://github.com/Makson61/learning-log.git
   cd learning-log
   cp .env.example .env
   nano .env
   ```

   Обязательно задайте свой `DJANGO_SECRET_KEY`
   (`python3 -c "import secrets; print(secrets.token_urlsafe(50))"`), `DJANGO_DEBUG=False`,
   свой домен в `DJANGO_ALLOWED_HOSTS` и `https://домен` в `DJANGO_CSRF_TRUSTED_ORIGINS`.

2. Запустите:

   ```sh
   docker compose up -d --build
   docker compose ps
   docker compose logs --tail=100 web
   ```

   Контейнер сам применяет миграции при каждом запуске (`start.sh` вызывает `manage.py prestart`),
   статические файлы собираются на этапе сборки образа. Если в `.env` заданы
   `DJANGO_SUPERUSER_USERNAME` и `DJANGO_SUPERUSER_PASSWORD`, администратор создаётся сам;
   иначе создайте его вручную:

   ```sh
   docker compose exec web python manage.py createsuperuser
   ```

3. Настройте HTTPS на обратном прокси. Пример для Nginx на том же сервере
   (`APP_BIND_IP=127.0.0.1`, `APP_PORT=8000`):

   ```nginx
   server {
       listen 80;
       server_name learning-log.example.ru;
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Затем выпустите сертификат: `sudo certbot --nginx -d learning-log.example.ru --redirect`.
   Если Nginx Proxy Manager стоит на другом сервере закрытой сети, укажите в `APP_BIND_IP`
   внутренний адрес сервера с Django и используйте его с портом 8000 в Proxy Host.

База SQLite лежит на именованном томе `learning_log_data` и переживает `docker compose up -d --build`.
Обновление: `git pull && docker compose up -d --build`.

## Переменные окружения

| Переменная | Нужна | Зачем |
|---|---|---|
| `DJANGO_SECRET_KEY` | на сервере обязательно | Секретный ключ. При `DEBUG=False` проект не запустится со значением по умолчанию |
| `DJANGO_DEBUG` | на сервере обязательно | `False` на сервере, по умолчанию `True` |
| `DJANGO_ALLOWED_HOSTS` | да | Домены через запятую |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | для HTTPS | `https://домен` через запятую |
| `SQLITE_PATH` | нет | Путь к файлу SQLite; в Docker это `/app/data/db.sqlite3` |
| `DATABASE_URL` | нет | PostgreSQL вместо SQLite: `postgresql://user:pass@host/db?sslmode=require` |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | нет | Администратор создаётся при запуске |
| `DEMO_DATA`, `DEMO_PASSWORD` | нет | `DEMO_DATA=True` создаёт пользователей `dmitry` и `olga` с этим паролем и демо-данными |
| `DJANGO_SECURE_SSL_REDIRECT` | нет | `True` - Django сам перенаправляет HTTP на HTTPS |
| `DJANGO_HSTS_SECONDS` | нет | Срок HSTS, по умолчанию 0 |
| `DJANGO_TIME_ZONE` | нет | Часовой пояс, по умолчанию `Europe/Moscow` |
| `APP_BIND_IP`, `APP_PORT` | нет | Где Compose публикует контейнер, по умолчанию `127.0.0.1:8000` |
| `PORT`, `WEB_CONCURRENCY`, `GUNICORN_THREADS` | нет | Порт, число процессов и потоков Gunicorn (8000, 2, 4) |

Файла `.env` в репозитории нет и не должно быть: он в `.gitignore`, а образец лежит в `.env.example`.

## Бесплатное размещение без своего сервера

Рабочая версия развёрнута бесплатно и не зависит от чьего-либо включённого компьютера:

- **Render**, бесплатный веб-сервис, собирает образ по тому же `Dockerfile` и выдаёт домен с HTTPS;
- **Neon**, бесплатный PostgreSQL без срока действия, хранит данные. Это важно: на бесплатном
  Render файловая система стирается при каждом перезапуске, поэтому SQLite там не подходит -
  пользователи и записи пропадали бы;
- бесплатный сервис засыпает после 15 минут без запросов, и первое открытие после сна занимает
  около 30 секунд. Workflow `.github/workflows/keepalive.yml` открывает `/healthz/` каждые
  10 минут по будням с 8:00 до 17:00 по Москве, поэтому днём сайт открывается сразу.
  Круглосуточно будить нельзя: на аккаунт даётся 750 бесплатных часов в месяц на все сервисы.
  Адрес `/healthz/` не обращается к базе, поэтому база в простое засыпает и не тратит свой лимит.

Как повторить:

1. В [Neon](https://neon.com) создайте проект (регион Frankfurt) и скопируйте строку подключения
   (**Pooled connection**).
2. В [Render](https://render.com) выберите **New → Blueprint** и укажите этот репозиторий:
   настройки возьмутся из `render.yaml`.
3. Заполните `DATABASE_URL`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` и
   `DEMO_PASSWORD`. Ключ `DJANGO_SECRET_KEY` Render сгенерирует сам.
4. Для автоматического обновления добавьте в репозиторий секрет `RENDER_API_KEY` и переменную
   `RENDER_SERVICE_ID`: после каждого push в `main` GitHub Actions сначала прогоняет тесты и
   сборку Docker и только при успехе запускает деплой.
