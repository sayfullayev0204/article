from django.shortcuts import render
from .models import Team,ArticleRequirement,News,Conference


def home(request):
    conferences = Conference.objects.filter(is_active=True).order_by('start_date')
    return render(request, 'index.html', {"home":"home",'conferences':conferences})

def current(request):
    current_conference = Conference.objects.filter(is_active=True).order_by('start_date').all()
    return render(request, 'current.html', {"current":"current", 'current_conference':current_conference}) 

def archive(request):
    archive_coneference = Conference.objects.filter(is_active=False).order_by('start_date').all()
    return render(request, 'archive.html', {"archive":"archive","archive_coneference":archive_coneference})

def team(request):
    teams = Team.objects.all()
    return render(request, 'team.html', {"team":"team", "teams":teams})

def police(request):
    polices = ArticleRequirement.objects.all()
    return render(request, 'police.html', {"police":"police", "polices":polices})

def about_journal(request):
    return render(request, 'about_journal.html', {"about":"about"})

def contact(request):
    return render(request, 'contact.html', {"about":"about"})

def news(request):
    news_items = News.objects.all().order_by('-created_at')
    return render(request, 'news.html', {"news":"news","news_items":news_items})

def news_detail(request, news_id):
    news = get_object_or_404(News, id=news_id)
    return render(request, 'news_detail.html', {'news': news})

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone

from .models import Article, Author, ArticleFile, ArticleAuthor, Conference
from .forms import ArticleForm, AuthorForm, ArticleFileForm, AuthorFormSet, FileFormSet

class ConferenceListView(ListView):
    model = Conference
    template_name = 'conferences/conference_list.html'
    context_object_name = 'conferences'
    
    def get_queryset(self):
        # Показываем только активные конференции
        return Conference.objects.filter(is_active=True).order_by('start_date')

class ConferenceDetailView(DetailView):
    model = Conference
    template_name = 'conferences/conference_detail.html'
    context_object_name = 'conference'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем статьи для этой конференции, если пользователь авторизован
        if self.request.user.is_authenticated:
            context['user_articles'] = Article.objects.filter(
                conference=self.object,
                created_by=self.request.user
            )
        return context

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        # Если пользователь авторизован, показываем только его статьи
        if self.request.user.is_authenticated:
            return Article.objects.filter(created_by=self.request.user).order_by('-created_at')
        return Article.objects.none()

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Проверяем, может ли пользователь редактировать статью
        article = self.object
        context['can_edit'] = (
            self.request.user.is_authenticated and 
            article.created_by == self.request.user and 
            article.status == 'draft'
        )
        return context

@login_required
def create_article(request, conference_id=None):
    initial_data = {}
    conference = None

    if conference_id:
        conference = get_object_or_404(Conference, pk=conference_id, is_active=True)
        if not conference.is_open_for_submission():
            messages.error(request, 'Эта конференция закрыта для подачи статей.')
            return redirect('conference_detail', pk=conference_id)
        initial_data['conference'] = conference

    if request.method == 'POST':
        article_form = ArticleForm(request.POST)
        
        if article_form.is_valid():
            with transaction.atomic():
                # Сохраняем статью
                article = article_form.save(commit=False)
                article.created_by = request.user
                article.status = 'draft'
                # Agar konferensiya mavjud bo‘lsa, uni qo‘shish
                if conference:
                    article.conference = conference
                article.save()
                
                # Обрабатываем авторов
                author_data = {
                    'given_name': request.POST.get('author_given_name'),
                    'family_name': request.POST.get('author_family_name'),
                    'email': request.POST.get('author_email'),
                    'country': request.POST.get('author_country'),
                    'affiliation': request.POST.get('author_affiliation'),
                }
                
                if all([author_data['given_name'], author_data['email'], author_data['country']]):
                    author, created = Author.objects.get_or_create(
                        email=author_data['email'],
                        defaults=author_data
                    )
                    ArticleAuthor.objects.create(
                        article=article,
                        author=author,
                        is_primary=True,
                        order=0
                    )
                
                # Обрабатываем файлы
                files = request.FILES.getlist('files')
                for file in files:
                    ArticleFile.objects.create(
                        article=article,
                        file=file,
                        file_name=file.name,
                        file_type='article_text'
                    )
                
                messages.success(request, 'Статья успешно создана!')
                return redirect('article_detail', pk=article.pk)
    else:
        article_form = ArticleForm(initial=initial_data)
    
    return render(request, 'articles/article_form.html', {
        'article_form': article_form,
        'conference': conference,
    })


@login_required
def edit_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    
    # Проверяем, имеет ли пользователь право редактировать статью
    if article.created_by != request.user:
        messages.error(request, 'У вас нет прав для редактирования этой статьи.')
        return redirect('article_detail', pk=article.pk)
    
    # Проверяем, можно ли редактировать статью (только в статусе черновика)
    if article.status != 'draft':
        messages.error(request, 'Нельзя редактировать статью, которая уже отправлена.')
        return redirect('article_detail', pk=article.pk)
    
    if request.method == 'POST':
        article_form = ArticleForm(request.POST, instance=article)
        author_formset = AuthorFormSet(request.POST, instance=article)
        file_formset = FileFormSet(request.POST, request.FILES, instance=article)
        
        if article_form.is_valid() and author_formset.is_valid() and file_formset.is_valid():
            with transaction.atomic():
                article_form.save()
                author_formset.save()
                file_formset.save()
                
                messages.success(request, 'Статья успешно обновлена!')
                return redirect('article_detail', pk=article.pk)
    else:
        article_form = ArticleForm(instance=article)
        author_formset = AuthorFormSet(instance=article)
        file_formset = FileFormSet(instance=article)
    
    return render(request, 'articles/article_edit.html', {
        'article_form': article_form,
        'author_formset': author_formset,
        'file_formset': file_formset,
        'article': article,
    })

@login_required
def submit_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    
    # Проверяем, имеет ли пользователь право отправлять статью
    if article.created_by != request.user:
        messages.error(request, 'У вас нет прав для отправки этой статьи.')
        return redirect('article_detail', pk=article.pk)
    
    # Проверяем, можно ли отправить статью (только в статусе черновика)
    if article.status != 'draft':
        messages.error(request, 'Эта статья уже отправлена.')
        return redirect('article_detail', pk=article.pk)
    
    # Проверяем, открыта ли конференция для подачи статей
    if not article.conference.is_open_for_submission():
        messages.error(request, 'Конференция закрыта для подачи статей.')
        return redirect('article_detail', pk=article.pk)
    
    # Проверяем, заполнены ли все обязательные поля
    if not article.title or not article.abstract or not article.keywords:
        messages.error(request, 'Пожалуйста, заполните все обязательные поля перед отправкой.')
        return redirect('edit_article', pk=article.pk)
    
    # Проверяем, есть ли хотя бы один автор
    if not article.authors.exists():
        messages.error(request, 'Пожалуйста, добавьте хотя бы одного автора перед отправкой.')
        return redirect('edit_article', pk=article.pk)
    
    # Проверяем, есть ли хотя бы один файл
    if not article.files.exists():
        messages.error(request, 'Пожалуйста, загрузите хотя бы один файл перед отправкой.')
        return redirect('edit_article', pk=article.pk)
    
    # Обновляем статус статьи
    article.status = 'submitted'
    article.submitted_at = timezone.now()
    article.save()
    
    messages.success(request, 'Статья успешно отправлена на рассмотрение!')
    return redirect('article_detail', pk=article.pk)

@login_required
def save_article_draft(request):
    if request.method == 'POST':
        # Extract basic article data
        article_data = {
            'title': request.POST.get('title', ''),
            'abstract': request.POST.get('abstract', ''),
            'keywords': request.POST.get('keywords', ''),
            'references': request.POST.get('references', ''),
            'start_date': request.POST.get('start_date', ''),
            'end_date': request.POST.get('end_date', ''),
            'cover_letter': request.POST.get('cover_letter', ''),
            'special_instructions': request.POST.get('special_instructions', ''),
        }
        
        conference_id = request.POST.get('conference')
        if conference_id:
            try:
                conference = Conference.objects.get(pk=conference_id)
                article_data['conference'] = conference
            except Conference.DoesNotExist:
                pass
        
        # Check if we're updating an existing draft or creating a new one
        article_id = request.POST.get('article_id')
        
        with transaction.atomic():
            if article_id:
                # Update existing draft
                try:
                    article = Article.objects.get(pk=article_id, created_by=request.user, status='draft')
                    for key, value in article_data.items():
                        if key != 'conference' and value:  # Skip empty values and conference
                            setattr(article, key, value)
                    if 'conference' in article_data:
                        article.conference = article_data['conference']
                    article.save()
                except Article.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Maqola topilmadi'
                    }, status=404)
            else:
                # Create new draft
                article = Article(
                    created_by=request.user,
                    status='draft',
                )
                
                # Set article fields
                for key, value in article_data.items():
                    if key != 'conference' and value:  # Skip empty values and conference
                        setattr(article, key, value)
                if 'conference' in article_data:
                    article.conference = article_data['conference']
                
                article.save()
            
            # Process author data if provided
            author_data = {
                'given_name': request.POST.get('author_given_name'),
                'family_name': request.POST.get('author_family_name'),
                'email': request.POST.get('author_email'),
                'country': request.POST.get('author_country'),
                'affiliation': request.POST.get('author_affiliation'),
            }
            
            if all([author_data['given_name'], author_data['email'], author_data['country']]):
                author, created = Author.objects.get_or_create(
                    email=author_data['email'],
                    defaults=author_data
                )
                
                # Check if this author is already linked to the article
                article_author, created = ArticleAuthor.objects.get_or_create(
                    article=article,
                    author=author,
                    defaults={'is_primary': True, 'order': 0}
                )
            
            # Process files if any
            files = request.FILES.getlist('files')
            for file in files:
                ArticleFile.objects.create(
                    article=article,
                    file=file,
                    file_name=file.name,
                    file_type='article_text'
                )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Maqola qoralama sifatida saqlandi',
                'article_id': article.id
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Noto\'g\'ri so\'rov'
    }, status=400)

