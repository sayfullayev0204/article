from django.urls import path
from .views import home,archive,current,police,team,about_journal,contact,news,news_detail
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('archive/', archive, name='archive'),
    path('current/', current, name='current'),
    path('police/', police, name='police'),
    path('team/', team, name='team'),
    path('about_journal/', about_journal, name='about_journal'),
    path('contact/', contact, name='contact'),
    path('news/', news, name='news'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    # Конференции
    path('profile/', views.ConferenceListView.as_view(), name='conference_list'),
    path('conferences/<int:pk>/', views.ConferenceDetailView.as_view(), name='conference_detail'),
    
    # Статьи
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('articles/create/', views.create_article, name='create_article'),
    path('conferences/<int:conference_id>/submit/', views.create_article, name='submit_to_conference'),
    path('articles/<int:pk>/edit/', views.edit_article, name='edit_article'),
    path('articles/<int:pk>/submit/', views.submit_article, name='submit_article'),


    path('articles/save-draft/', views.save_article_draft, name='save_article_draft'),
]