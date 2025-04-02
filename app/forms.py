from django import forms
from django.utils import timezone
from .models import Article, Author, ArticleFile, ArticleAuthor, Conference

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['given_name', 'family_name', 'preferred_name', 'email', 
                  'country', 'affiliation', 'role']
        widgets = {
            'given_name': forms.TextInput(attrs={'class': 'form-control'}),
            'family_name': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Konferensiya tanlash uchun moslashtirilgan variantlar
            self.fields['conference'].widget = forms.Select(attrs={'class': 'form-control'})
            self.fields['conference'].queryset = Conference.objects.all()

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'abstract', 'keywords', 'references', 
                  'conference', 'start_date', 'end_date', 'cover_letter', 'special_instructions']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'references': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conference': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только активные конференции, открытые для подачи статей
        self.fields['conference'].queryset = Conference.objects.filter(is_active=True)

class ArticleFileForm(forms.ModelForm):
    class Meta:
        model = ArticleFile
        fields = ['file', 'file_type', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# Формсет для нескольких авторов
AuthorFormSet = forms.inlineformset_factory(
    Article, 
    ArticleAuthor,
    fields=['author', 'is_primary', 'order'],
    extra=1,
    can_delete=True
)

# Формсет для нескольких файлов
FileFormSet = forms.inlineformset_factory(
    Article, 
    ArticleFile,
    form=ArticleFileForm,
    extra=1,
    can_delete=True
)

