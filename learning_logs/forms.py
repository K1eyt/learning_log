from django import forms

from .models import Entry, Topic


class TopicForm(forms.ModelForm):
    """Название темы. Владелец подставляется в представлении."""

    class Meta:
        model = Topic
        fields = ['text']
        labels = {'text': 'Название темы'}
        widgets = {'text': forms.TextInput(attrs={'placeholder': 'Django, английский, гитара...'})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_text(self):
        """Проверяет, что у этого пользователя ещё нет темы с таким названием."""
        text = self.cleaned_data['text'].strip()
        if self.owner is None:
            return text
        duplicates = Topic.objects.filter(owner=self.owner, text__iexact=text)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('Тема с таким названием у вас уже есть.')
        return text


class EntryForm(forms.ModelForm):
    """Текст записи. Тема и даты задаются представлением."""

    class Meta:
        model = Entry
        fields = ['text']
        labels = {'text': 'Что вы узнали?'}
        widgets = {'text': forms.Textarea(attrs={
            'rows': 10, 'placeholder': 'Своими словами - так лучше запомнится.',
        })}
