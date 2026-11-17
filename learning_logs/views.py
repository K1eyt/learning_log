"""
Представления учебного журнала.

Тема и запись всегда берутся вместе с условием по владельцу, поэтому чужой
или несуществующий идентификатор даёт одинаковый ответ 404, а спрятанная
в шаблоне ссылка ничего не защищает и не должна защищать.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST, require_http_methods

from .forms import EntryForm, TopicForm
from .models import Entry, Topic

ENTRIES_PER_PAGE = 8


def get_topic(request, topic_id):
    """Тема текущего пользователя или 404."""
    return get_object_or_404(Topic, pk=topic_id, owner=request.user)


def get_entry(request, entry_id):
    """Запись из темы текущего пользователя или 404."""
    return get_object_or_404(Entry.objects.select_related('topic'), pk=entry_id,
                             topic__owner=request.user)


def index(request):
    """Домашняя страница: приглашение для гостя, сводка для своего."""
    context = {}
    if request.user.is_authenticated:
        topics = Topic.objects.owned_by(request.user)
        context = {
            'favorites': topics.active().filter(is_favorite=True).with_counters()[:4],
            'total_topics': topics.active().count(),
            'total_entries': Entry.objects.filter(topic__owner=request.user).count(),
            'total_archived': topics.filter(is_archived=True).count(),
        }
    return render(request, 'learning_logs/index.html', context)


@login_required
def topics(request):
    """Список тем: обычные или архивные, с поиском по темам и записям."""
    archived = request.GET.get('archived') == '1'
    query = request.GET.get('q', '').strip()

    found = Topic.objects.owned_by(request.user).filter(is_archived=archived)
    if query:
        matched = Topic.objects.owned_by(request.user).filter(
            Q(text__icontains=query) | Q(entries__text__icontains=query),
        ).values('pk')
        found = found.filter(pk__in=matched)

    counts = Topic.objects.owned_by(request.user).aggregate(
        active=Count('pk', filter=Q(is_archived=False)),
        archived=Count('pk', filter=Q(is_archived=True)),
    )
    return render(request, 'learning_logs/topics.html', {
        'topics': found.with_counters(),
        'archived': archived,
        'query': query,
        'counts': counts,
    })


@login_required
def topic(request, topic_id):
    """Одна тема со всеми её записями постранично."""
    current = get_topic(request, topic_id)
    page = Paginator(current.entries.all(), ENTRIES_PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'learning_logs/topic.html', {'topic': current, 'entries': page, 'page_obj': page})


@login_required
def new_topic(request):
    """Создаёт новую тему."""
    if request.method != 'POST':
        # Запрос без данных: показываем пустую форму.
        form = TopicForm(owner=request.user)
    else:
        # Пришли данные POST: проверяем и сохраняем.
        form = TopicForm(data=request.POST, owner=request.user)
        if form.is_valid():
            created = form.save(commit=False)
            created.owner = request.user
            created.save()
            messages.success(request, f'Тема «{created}» создана.')
            return redirect('learning_logs:topic', topic_id=created.pk)

    return render(request, 'learning_logs/new_topic.html', {'form': form})


@login_required
def rename_topic(request, topic_id):
    """Переименовывает существующую тему."""
    current = get_topic(request, topic_id)
    if request.method != 'POST':
        form = TopicForm(instance=current, owner=request.user)
    else:
        form = TopicForm(instance=current, data=request.POST, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Название темы сохранено.')
            return redirect('learning_logs:topic', topic_id=current.pk)

    return render(request, 'learning_logs/rename_topic.html', {'form': form, 'topic': current})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_topic(request, topic_id):
    """GET показывает подтверждение, удаляет только POST."""
    current = get_topic(request, topic_id)
    if request.method == 'POST':
        current.delete()
        messages.success(request, f'Тема «{current}» удалена вместе с записями.')
        return redirect('learning_logs:topics')

    return render(request, 'learning_logs/confirm_delete.html', {
        'title': 'Удалить тему?',
        'name': current.text,
        'note': f'Записей внутри: {current.entries.count()}. Восстановить их будет нельзя.',
        'hint': 'Если тема просто мешает в списке, уберите её в архив вместо удаления.',
        'back_url': current.get_absolute_url(),
    })


@login_required
@require_POST
def toggle_favorite(request, topic_id):
    """Добавляет тему в избранное или убирает из него."""
    current = get_topic(request, topic_id)
    current.is_favorite = not current.is_favorite
    current.save(update_fields=['is_favorite'])
    messages.info(request, 'Тема в избранном.' if current.is_favorite else 'Тема убрана из избранного.')
    return redirect(request.POST.get('next') or 'learning_logs:topics')


@login_required
@require_POST
def toggle_archive(request, topic_id):
    """Убирает тему в архив или возвращает обратно."""
    current = get_topic(request, topic_id)
    current.is_archived = not current.is_archived
    if current.is_archived:
        current.is_favorite = False
    current.save(update_fields=['is_archived', 'is_favorite'])
    messages.info(request, 'Тема в архиве.' if current.is_archived else 'Тема возвращена из архива.')
    return redirect('learning_logs:topics')


@login_required
def export_topic(request, topic_id):
    """Отдаёт тему текстовым файлом: записи от старых к новым."""
    current = get_topic(request, topic_id)
    lines = [f'# {current.text}', '']
    for entry in current.entries.order_by('date_added'):
        lines += [f'## {entry.date_added:%d.%m.%Y %H:%M}', '', entry.text, '']

    name = slugify(current.text, allow_unicode=True) or f'topic-{current.pk}'
    response = HttpResponse('\n'.join(lines), content_type='text/markdown; charset=utf-8')
    # filename* с кодировкой UTF-8 нужен, чтобы русское имя файла не потерялось.
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{name}.md"
    return response


@login_required
def new_entry(request, topic_id):
    """Добавляет запись в конкретную тему."""
    current = get_topic(request, topic_id)

    if request.method != 'POST':
        form = EntryForm()
    else:
        form = EntryForm(data=request.POST)
        if form.is_valid():
            created = form.save(commit=False)
            created.topic = current
            created.save()
            messages.success(request, 'Запись добавлена.')
            return redirect('learning_logs:topic', topic_id=current.pk)

    return render(request, 'learning_logs/new_entry.html', {'topic': current, 'form': form})


@login_required
def edit_entry(request, entry_id):
    """Редактирует существующую запись."""
    entry = get_entry(request, entry_id)

    if request.method != 'POST':
        # Первый запрос: форма заполняется текущим текстом записи.
        form = EntryForm(instance=entry)
    else:
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись сохранена.')
            return redirect('learning_logs:topic', topic_id=entry.topic_id)

    return render(request, 'learning_logs/edit_entry.html', {'entry': entry, 'topic': entry.topic, 'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_entry(request, entry_id):
    """GET показывает подтверждение, удаляет только POST."""
    entry = get_entry(request, entry_id)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Запись удалена.')
        return redirect('learning_logs:topic', topic_id=entry.topic_id)

    return render(request, 'learning_logs/confirm_delete.html', {
        'title': 'Удалить запись?',
        'name': str(entry),
        'note': f'Из темы «{entry.topic}».',
        'back_url': entry.topic.get_absolute_url(),
    })
