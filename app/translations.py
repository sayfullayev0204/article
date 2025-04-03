from modeltranslation.translator import register, TranslationOptions
from .models import (
    Conference, Author, Article, Team, 
    ArticleRequirement, News
)

@register(Conference)
class ConferenceTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'location')

@register(Author)
class AuthorTranslationOptions(TranslationOptions):
    fields = ('given_name', 'family_name', 'preferred_name', 'bio', 'affiliation')

@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ('title', 'abstract', 'keywords', 'references', 'cover_letter', 'special_instructions')

@register(Team)
class TeamTranslationOptions(TranslationOptions):
    fields = ('fullname', 'specialty', 'affiliation')

@register(ArticleRequirement)
class ArticleRequirementTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'summary', 'content')

