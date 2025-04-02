from django.contrib import admin
from .models import Author, Article, ArticleAuthor, ArticleFile, Conference,Team


class ArticleAuthorInline(admin.TabularInline):
    model = ArticleAuthor
    extra = 1

class ArticleFileInline(admin.TabularInline):
    model = ArticleFile
    extra = 1

class ArticleInline(admin.TabularInline):
    model = Article
    extra = 0
    fields = ('title', 'status', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')
    show_change_link = True
    can_delete = False

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'submission_deadline', 'is_active', 'is_open_for_submission')
    list_filter = ('is_active', 'start_date', 'end_date', 'submission_deadline')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    inlines = [ArticleInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'image')
        }),
        ('Даты и место', {
            'fields': ('start_date', 'end_date', 'submission_deadline', 'location')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'affiliation', 'country', 'role')
    search_fields = ('given_name', 'family_name', 'preferred_name', 'email')
    list_filter = ('role', 'country', 'include_in_lists')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference', 'status', 'start_date', 'end_date', 'created_by', 'created_at')
    search_fields = ('title', 'abstract', 'keywords')
    list_filter = ('status', 'conference', 'start_date', 'end_date')
    date_hierarchy = 'created_at'
    inlines = [ArticleAuthorInline, ArticleFileInline]
    readonly_fields = ('created_at', 'updated_at', 'submitted_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'abstract', 'keywords', 'references', 'conference')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date')
        }),
        ('Для редакторов', {
            'fields': ('cover_letter', 'special_instructions')
        }),
        ('Статус и метаданные', {
            'fields': ('status', 'created_by', 'created_at', 'updated_at', 'submitted_at')
        }),
    )

@admin.register(ArticleFile)
class ArticleFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'article', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('file_name', 'description', 'article__title')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'specialty', 'affiliation', 'contact']

from .models import ArticleRequirement

admin.site.register(ArticleRequirement)
from django.contrib import admin
from .models import News

admin.site.register(News)