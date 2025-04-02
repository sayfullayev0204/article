from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import path,include
from django.contrib import admin
from django.contrib.auth.views import LogoutView, LoginView


def register(request):
    return render(request, 'index.html')


urlpatterns = [
   path('',include('app.urls')),
   path('accounts/',include('accounts.urls')),
   path('admin/', admin.site.urls)
] 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


