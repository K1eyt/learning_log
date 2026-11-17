"""Корневые маршруты проекта «Журнал знаний»."""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

admin.site.site_header = 'Учебный журнал: администрирование'
admin.site.site_title = 'Учебный журнал'
admin.site.index_title = 'Данные сайта'


def healthz(_request):
    """Проверка живости для Docker и хостинга: не трогает базу данных."""
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('healthz/', healthz, name='healthz'),
    path('', include('learning_logs.urls')),
]
