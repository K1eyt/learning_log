from django.contrib import admin

from .models import Entry, Topic


class EntryInline(admin.StackedInline):
    model = Entry
    extra = 0
    fields = ('text',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('text', 'owner', 'entries_count', 'is_favorite', 'is_archived', 'date_added')
    list_filter = ('is_archived', 'is_favorite', 'date_added', 'owner')
    list_editable = ('is_favorite', 'is_archived')
    search_fields = ('text', 'owner__username')
    list_select_related = ('owner',)
    date_hierarchy = 'date_added'
    inlines = [EntryInline]

    def get_queryset(self, request):
        return super().get_queryset(request).with_counters()

    @admin.display(description='записей', ordering='entries_total')
    def entries_count(self, topic):
        return topic.entries_total


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'topic', 'topic_owner', 'date_added')
    list_filter = ('date_added', 'topic__owner')
    search_fields = ('text', 'topic__text')
    list_select_related = ('topic__owner',)
    date_hierarchy = 'date_added'

    @admin.display(description='владелец', ordering='topic__owner__username')
    def topic_owner(self, entry):
        return entry.topic.owner
