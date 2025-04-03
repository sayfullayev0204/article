from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from config import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class Conference(models.Model):
    """Konferensiyalar uchun model"""
    title = models.CharField(max_length=255, verbose_name="Konferensiya nomi")
    description = models.TextField(verbose_name="Tavsif")
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    end_date = models.DateField(verbose_name="Tugash sanasi")
    submission_deadline = models.DateField(verbose_name="Maqolalar topshirish oxirgi muddati")
    location = models.CharField(max_length=255, verbose_name="O'tkaziladigan joy")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    image = models.ImageField(upload_to='conference_images/', blank=True, null=True, verbose_name="Rasm")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")
    price = models.CharField(max_length=20, blank=True, null=True)
    def is_open_for_submission(self):
        """Konferensiya maqola topshirish uchun ochiq yoki yo'qligini tekshiradi"""
        return self.is_active and self.submission_deadline >= timezone.now().date()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Jurnal soni"
        verbose_name_plural = "Jurnal soni"
        ordering = ['-start_date']


class AuthorManager(BaseUserManager):
    def create_user(self, email, given_name, family_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email majburiy!")
        email = self.normalize_email(email)
        user = self.model(email=email, given_name=given_name, family_name=family_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, given_name, family_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, given_name, family_name, password, **extra_fields)

class Author(AbstractBaseUser):
    """Maqola mualliflari uchun model"""
    given_name = models.CharField(max_length=100, verbose_name="Ism")
    family_name = models.CharField(max_length=100, blank=True, verbose_name="Familiya")
    preferred_name = models.CharField(max_length=200, blank=True, verbose_name="Tanlangan ism")
    email = models.EmailField(unique=True, verbose_name="Email")
    country = models.CharField(max_length=100, verbose_name="Davlat")
    homepage = models.URLField(blank=True, verbose_name="Shaxsiy sahifa")
    orcid = models.CharField(max_length=50, blank=True, verbose_name="ORCID ID")
    bio = models.TextField(blank=True, verbose_name="Biografiya")
    affiliation = models.CharField(max_length=200, blank=True, verbose_name="Tashkilot")
    role = models.CharField(
        max_length=20,
        choices=[('author', 'Muallif'), ('translator', 'Tarjimon')],
        default='author',
        verbose_name="Rol"
    )
    include_in_lists = models.BooleanField(default=True, verbose_name="Nashrlar ro'yxatiga kiritish")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    # Django autentifikatsiyasi uchun majburiy maydonlar
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = AuthorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['given_name', 'family_name']

    def __str__(self):
        full_name = f"{self.given_name} {self.family_name}".strip()
        return self.preferred_name or full_name

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    # Qo‘shimcha metodlar (admin panel uchun zarur)
    def get_all_permissions(self, obj=None):
        return set()  # Bo‘sh ruxsatlar to‘plami qaytariladi

    def get_user_permissions(self, obj=None):
        return set()  # Bo‘sh ruxsatlar to‘plami qaytariladi

    class Meta:
        verbose_name = "Foydalanuvchilar"
        verbose_name_plural = "Foydalanuvchilar"


class Article(models.Model):
    """Maqolalar uchun model"""
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('submitted', 'Yuborilgan'),
        ('under_review', "Ko'rib chiqilmoqda"),
        ('payment', "To'lov qilish"),
        ('accepted', 'Qabul qilingan'),
        ('rejected', 'Rad etilgan'),
        ('published', 'Chop etilgan'),
    ]

    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    abstract = models.TextField(verbose_name="Annotatsiya")
    keywords = models.CharField(max_length=255, verbose_name="Kalit so'zlar")
    references = models.TextField(blank=True, verbose_name="Havolalar")

    # Konferensiya bilan bog'lanish
    conference = models.ForeignKey(
        Conference, 
        on_delete=models.CASCADE, 
        related_name='articles',  # 'Konferensiya' o‘rniga 'articles' ishlatildi
        verbose_name="Konferensiya",
        null=True,  # Qo‘shildi
        blank=True  # Qo‘shildi
    )

    # Boshlanish va tugash sanalari
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    end_date = models.DateField(blank=True, null=True, verbose_name="Tugash sanasi")

    # Mualliflar bilan bog'lanish (ko'p-ko'p)
    authors = models.ManyToManyField(
        Author, 
        through='ArticleAuthor',
        related_name='articles',
        verbose_name="Mualliflar"
    )

    # Tahrirchilar uchun ma'lumot
    cover_letter = models.TextField(blank=True, verbose_name="Qo'shimcha xat")
    special_instructions = models.TextField(blank=True, verbose_name="Maxsus ko'rsatmalar")

    # Metama'lumotlar
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Holat"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='created_articles',
        verbose_name="Yaratuvchi"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="Yuborilgan sana")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Maqola"
        verbose_name_plural = "Maqolalar"


class ArticleAuthor(models.Model):
    """Maqolalar va mualliflar o'rtasidagi bog'lovchi model"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False, verbose_name="Asosiy muallif")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        ordering = ['order']
        unique_together = ['article', 'author']
        verbose_name = "Maqola muallifi"
        verbose_name_plural = "Maqola mualliflari"


class ArticleFile(models.Model):
    """Maqolaga biriktirilgan fayllar uchun model"""
    FILE_TYPE_CHOICES = [
        ('article_text', 'Maqola matni'),
        ('dataset', "Ma'lumotlar to'plami"),
        ('supplementary', 'Qo‘shimcha material'),
        ('image', 'Rasm'),
        ('other', 'Boshqa'),
    ]

    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name="Maqola"
    )
    file = models.FileField(upload_to='article_files/%Y/%m/', verbose_name="Fayl")
    file_name = models.CharField(max_length=255, verbose_name="Fayl nomi")
    file_type = models.CharField(
        max_length=20, 
        choices=FILE_TYPE_CHOICES,
        default='other',
        verbose_name="Fayl turi"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan sana")

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Maqola fayli"
        verbose_name_plural = "Maqola fayllari"

class Team(models.Model):
    fullname = models.CharField(max_length=100)
    specialty = models.CharField(max_length=200)
    affiliation = models.CharField(max_length=200)
    contact = models.CharField(max_length=200)
    image = models.ImageField(upload_to='team/', blank=True, null=True)

    def __str__(self):
        return self.fullname
    
    class Meta:
        verbose_name = "Taqriz a'zolari"
        verbose_name_plural = "Taqriz a'zolari"

class ArticleRequirement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=0)
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Maqola Talablari"
        verbose_name_plural = "Maqola Talablari"

class ArticleRequirementFile(models.Model):
    file = models.FileField(upload_to='article_requirement_files/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        verbose_name = "Maqola Talablari Fayllari"
        verbose_name_plural = "Maqola Talablari Fayllari"

class News(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Yangiliklar"
        verbose_name_plural = "Yangiliklar"

class Payment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Maqola")
    card_number = models.CharField(max_length=20, verbose_name="Karta raqami")  # Xato tuzatildi
    price = models.CharField(max_length=20, verbose_name="Narx")
    description = models.TextField(verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # To'lov saqlanganda maqola statusini "accepted" ga o'zgartirish
        self.article.status = 'accepted'
        self.article.save()

    def __str__(self):
        return f"{self.article.title} - {self.created_at}"

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"