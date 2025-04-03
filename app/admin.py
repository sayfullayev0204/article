from django.contrib import admin
from .models import Author, Article, ArticleAuthor, ArticleFile, Conference,Team,Payment,ArticleRequirement,ArticleRequirementFile, News
from django.contrib.auth.models import Group

admin.site.register(ArticleRequirementFile)


admin.site.unregister(Group)

# Conference admin
@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'submission_deadline', 'is_active')
    list_filter = ('is_active', 'start_date', 'submission_deadline')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image','price')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'submission_deadline')
        }),
        ('Details', {
            'fields': ('location', 'is_active')
        }),
    )

from django.contrib import admin
from .models import Author, Article, ArticleAuthor, ArticleFile

# Inline klasslar
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

# Author admin
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('email', 'given_name', 'family_name', 'country', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role')
    search_fields = ('email', 'given_name', 'family_name', 'preferred_name')
    ordering = ('email',)
    fieldsets = (
        (None, {
            'fields': ('email', 'given_name', 'family_name', 'preferred_name', 'password')
        }),
        ('Personal Info', {
            'fields': ('country', 'homepage', 'orcid', 'bio', 'affiliation')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role')
        }),
        ('Preferences', {
            'fields': ('include_in_lists',)
        }),
    )

# Article admin (ArticleAuthor va ArticleFile inline sifatida qo‘shiladi)
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'conference', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'conference', 'created_at')
    search_fields = ('title', 'abstract', 'keywords')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ArticleAuthorInline, ArticleFileInline]  # Inline qo‘shildi
    fieldsets = (
        (None, {
            'fields': ('title', 'abstract', 'keywords', 'conference')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'submitted_at')
        }),
        ('Editor Info', {
            'fields': ('cover_letter', 'special_instructions', 'references')
        }),
        ('Metadata', {
            'fields': ('status', 'created_by')
        }),
    )

# ArticleAuthor va ArticleFile uchun alohida admin ro‘yxatlari olib tashlanadi
# Agar kerak bo‘lsa, faqat inline sifatida ishlatiladi
# Team admin
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'specialty', 'affiliation')
    search_fields = ('fullname', 'specialty', 'affiliation', 'contact')
    fieldsets = (
        (None, {
            'fields': ('fullname', 'specialty', 'affiliation', 'contact', 'image')
        }),
    )

# ArticleRequirement admin
@admin.register(ArticleRequirement)
class ArticleRequirementAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    search_fields = ('title', 'description')
    ordering = ('order',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'order')
        }),
    )

# News admin
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'summary', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'summary', 'content', 'image')
        }),
    )

admin.site.register(Payment)