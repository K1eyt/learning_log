"""Схемы URL приложения learning_logs."""
from django.urls import path

from . import views

app_name = 'learning_logs'

urlpatterns = [
    # Домашняя страница
    path('', views.index, name='index'),
    # Список тем пользователя
    path('topics/', views.topics, name='topics'),
    # Отдельная тема со всеми записями
    path('topics/<int:topic_id>/', views.topic, name='topic'),
    path('topics/<int:topic_id>/rename/', views.rename_topic, name='rename_topic'),
    path('topics/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),
    path('topics/<int:topic_id>/export/', views.export_topic, name='export_topic'),
    path('topics/<int:topic_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('topics/<int:topic_id>/archive/', views.toggle_archive, name='toggle_archive'),
    # Новая тема
    path('new_topic/', views.new_topic, name='new_topic'),
    # Новая запись по теме
    path('new_entry/<int:topic_id>/', views.new_entry, name='new_entry'),
    # Редактирование записи
    path('edit_entry/<int:entry_id>/', views.edit_entry, name='edit_entry'),
    path('entries/<int:entry_id>/delete/', views.delete_entry, name='delete_entry'),
]
