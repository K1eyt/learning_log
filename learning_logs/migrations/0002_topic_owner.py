"""
Добавляет владельца темы.

Постоянного default=1 в модели нет: поле сначала создаётся необязательным,
затем существующие темы получают существующего пользователя, и только после
этого поле становится обязательным. Так миграция работает и на пустой базе,
и на базе с уже накопленными данными.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def fill_owner(apps, schema_editor):
    Topic = apps.get_model('learning_logs', 'Topic')
    without_owner = Topic.objects.filter(owner__isnull=True)
    if not without_owner.exists():
        return

    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    owner = (User.objects.filter(is_superuser=True).order_by('pk').first()
             or User.objects.order_by('pk').first())
    if owner is None:
        # Пользователей нет вообще: заводим неактивную учётную запись без пароля.
        owner = User.objects.create(username='archive_owner', is_active=False, password='!')
    without_owner.update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(fill_owner, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='topic',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
    ]
