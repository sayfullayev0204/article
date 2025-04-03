from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
import json
from .models import Article, ArticleRequirementFile, Author, ArticleFile, ArticleAuthor, Conference,Payment,News,Team,ArticleRequirement
from .forms import ArticleForm, AuthorForm, ArticleFileForm, AuthorFormSet, FileFormSet


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
    polices_file = ArticleRequirementFile.objects.first()
    return render(request, 'police.html', {
        "police": "police",
        "polices": polices,
        "polices_file": polices_file
    })

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


class ConferenceListView(ListView):
    model = Conference
    template_name = 'conferences/conference_list.html'
    context_object_name = 'conferences'
    
    def get_queryset(self):
        # Faqat faol konferensiyalarni ko'rsatamiz
        return Conference.objects.filter(is_active=True).order_by('start_date')

class ConferenceDetailView(DetailView):
    model = Conference
    template_name = 'conferences/conference_detail.html'
    context_object_name = 'conference'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Foydalanuvchi tizimga kirgan bo'lsa, uning maqolalarini qo'shamiz
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
        # Agar foydalanuvchi tizimga kirgan bo'lsa, faqat uning maqolalarini ko'rsatamiz
        if self.request.user.is_authenticated:
            return Article.objects.filter(created_by=self.request.user).order_by('-created_at')
        return Article.objects.none()

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Foydalanuvchi maqolani tahrirlashi mumkinligini tekshiramiz
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
            messages.error(request, 'Bu konferensiya maqola topshirish uchun yopilgan.')
            return redirect('conference_detail', pk=conference_id)
        initial_data['conference'] = conference

    # Forma yuborilganini qayta ishlash
    if request.method == 'POST':
        article_form = ArticleForm(request.POST)
        
        if article_form.is_valid():
            with transaction.atomic():
                # Maqolani saqlash
                article = article_form.save(commit=False)
                article.created_by = request.user
                article.status = 'draft'
                
                # Konferensiya mavjud bo'lsa, uni qo'shamiz
                if conference:
                    article.conference = conference
                article.save()
                
                # Formadan mualliflarni qayta ishlash
                contributors_data = request.POST.getlist('contributors[]')
                if contributors_data:
                    for i, contributor_json in enumerate(contributors_data):
                        try:
                            contributor = json.loads(contributor_json)
                            author_data = {
                                'given_name': contributor.get('given_name', ''),
                                'family_name': contributor.get('family_name', ''),
                                'email': contributor.get('email', ''),
                                'country': contributor.get('country', ''),
                                'affiliation': contributor.get('affiliation', ''),
                                'orcid': contributor.get('orcid', ''),
                                'homepage': contributor.get('homepage', ''),
                                'bio': contributor.get('bio', ''),
                            }
                            
                            if all([author_data['given_name'], author_data['email'], author_data['country']]):
                                author, created = Author.objects.get_or_create(
                                    email=author_data['email'],
                                    defaults=author_data
                                )
                                
                                # Agar yaratilmagan bo'lsa, muallif ma'lumotlarini yangilaymiz
                                if not created:
                                    for key, value in author_data.items():
                                        if value:  # Faqat bo'sh bo'lmagan qiymatlarni yangilaymiz
                                            setattr(author, key, value)
                                    author.save()
                                
                                ArticleAuthor.objects.create(
                                    article=article,
                                    author=author,
                                    is_primary=(i == 0),  # Birinchi muallif asosiy hisoblanadi
                                    order=i
                                )
                        except json.JSONDecodeError:
                            continue
                
                # Fayllarni qayta ishlash
                files = request.FILES.getlist('files')
                for file in files:
                    ArticleFile.objects.create(
                        article=article,
                        file=file,
                        file_name=file.name,
                        file_type='article_text'
                    )
                
                if request.POST.get('submit_type') == 'submit':
                    # Agar foydalanuvchi yakuniy yuborish tugmasini bosgan bo'lsa
                    article.status = 'submitted'
                    article.submitted_at = timezone.now()
                    article.save()
                    messages.success(request, 'Maqola muvaffaqiyatli yuborildi!')
                else:
                    messages.success(request, 'Maqola qoralama sifatida saqlandi!')
                
                return redirect('article_detail', pk=article.pk)
        else:
            # Forma tekshiruvi muvaffaqiyatsiz tugadi
            for field, errors in article_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        article_form = ArticleForm(initial=initial_data)
    
    return render(request, 'articles/article_form.html', {
        'article_form': article_form,
        'conference': conference,
    })

@login_required
def edit_article(request, pk):
    article = get_object_or_404(Article, pk=pk)
    
    # Foydalanuvchining maqolani tahrirlash huquqini tekshiramiz
    if article.created_by != request.user:
        messages.error(request, 'Sizda ushbu maqolani tahrirlash huquqi yo\'q.')
        return redirect('article_detail', pk=article.pk)
    
    # Maqolani tahrirlash mumkinligini tekshiramiz (faqat qoralama holatida)
    if article.status != 'draft':
        messages.error(request, 'Yuborilgan maqolani tahrirlab bo\'lmaydi.')
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
                
                messages.success(request, 'Maqola muvaffaqiyatli yangilandi!')
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
    
    # Foydalanuvchining maqolani yuborish huquqini tekshiramiz
    if article.created_by != request.user:
        messages.error(request, 'Sizda ushbu maqolani yuborish huquqi yo\'q.')
        return redirect('article_detail', pk=article.pk)
    
    # Maqolani yuborish mumkinligini tekshiramiz (faqat qoralama holatida)
    if article.status != 'draft':
        messages.error(request, 'Bu maqola allaqachon yuborilgan.')
        return redirect('article_detail', pk=article.pk)
    
    # Konferensiya maqola topshirish uchun ochiqligini tekshiramiz
    if not article.conference.is_open_for_submission():
        messages.error(request, 'Konferensiya maqola topshirish uchun yopilgan.')
        return redirect('article_detail', pk=article.pk)
    
    # Barcha majburiy maydonlar to'ldirilganligini tekshiramiz
    if not article.title or not article.abstract or not article.keywords:
        messages.error(request, 'Iltimos, yuborishdan oldin barcha majburiy maydonlarni to\'ldiring.')
        return redirect('edit_article', pk=article.pk)
    
    # Kamida bitta muallif mavjudligini tekshiramiz
    if not article.authors.exists():
        messages.error(request, 'Iltimos, yuborishdan oldin kamida bitta muallif qo\'shing.')
        return redirect('edit_article', pk=article.pk)
    
    # Kamida bitta fayl mavjudligini tekshiramiz
    if not article.files.exists():
        messages.error(request, 'Iltimos, yuborishdan oldin kamida bitta fayl yuklang.')
        return redirect('edit_article', pk=article.pk)
    
    # Maqola holatini yangilaymiz
    article.status = 'submitted'
    article.submitted_at = timezone.now()
    article.save()
    
    messages.success(request, 'Maqola muvaffaqiyatli ko\'rib chiqish uchun yuborildi!')
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


@login_required
def get_article_draft(request, article_id):
    try:
        article = Article.objects.get(pk=article_id, created_by=request.user, status='draft')
        
        # Mualliflarni olamiz
        article_authors = ArticleAuthor.objects.filter(article=article).order_by('order')
        contributors = []
        
        for article_author in article_authors:
            author = article_author.author
            contributors.append({
                'given_name': author.given_name,
                'family_name': author.family_name,
                'email': author.email,
                'country': author.country,
                'affiliation': author.affiliation,
                'orcid': author.orcid,
                'homepage': author.homepage,
                'bio': author.bio,
                'is_primary': article_author.is_primary,
                'order': article_author.order
            })
        
        # Fayllarni olamiz
        article_files = ArticleFile.objects.filter(article=article)
        files = []
        
        for file in article_files:
            files.append({
                'id': file.id,
                'name': file.file_name,
                'url': file.file.url if file.file else None,
                'type': file.file_type
            })
        
        return JsonResponse({
            'status': 'success',
            'article': {
                'id': article.id,
                'title': article.title,
                'abstract': article.abstract,
                'keywords': article.keywords,
                'references': article.references,
                'start_date': article.start_date.strftime('%Y-%m-%d') if article.start_date else None,
                'end_date': article.end_date.strftime('%Y-%m-%d') if article.end_date else None,
                'cover_letter': article.cover_letter,
                'special_instructions': article.special_instructions,
                'conference_id': article.conference.id if article.conference else None,
                'last_saved': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else None
            },
            'contributors': contributors,
            'files': files
        })
    except Article.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Maqola topilmadi'
        }, status=404)

@login_required
def make_payment(request, article_id):
    article = get_object_or_404(Article, id=article_id, created_by=request.user)
    conference = article.conference

    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        description = request.POST.get('description')
        price = conference.price if conference and conference.price else "0"  # Agar conference bo'lmasa 0

        payment = Payment(
            article=article,
            card_number=card_number,
            price=price,
            description=description
        )
        payment.save()
        messages.success(request, "To'lov muvaffaqiyatli amalga oshirildi!")
        return redirect(f"{reverse('profile')}?tab=business")

    context = {
        'article': article,
        'price': conference.price if conference else "0"
    }
    return render(request, 'articles/payment_form.html', context)

from django.db.models import Q
from django.shortcuts import render
from .models import Article, Author

def search(request):
    query = request.GET.get('q', '')
    
    if query:
        # Search articles by title, abstract, or keywords
            articles = Article.objects.filter(
            Q(title__icontains=query) |
            Q(abstract__icontains=query) |
            Q(keywords__icontains=query) |
            Q(authors__given_name__icontains=query) |
            Q(authors__family_name__icontains=query) |
            Q(authors__preferred_name__icontains=query) |
            Q(authors__email__icontains=query) |
            Q(authors__affiliation__icontains=query)
        ).distinct()

    else:
        articles = Article.objects.none()
    
    context = {
        'query': query,
        'articles': articles
    }
    
    return render(request, 'articles/search_results.html', context)
