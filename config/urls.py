from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import path,include
from django.contrib import admin
from django.contrib.auth.views import LogoutView, LoginView
from django.conf.urls.i18n import i18n_patterns


urlpatterns = i18n_patterns(
   path('',include('app.urls')),
   path('accounts/',include('accounts.urls')),
   path('admin/', admin.site.urls)
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



# i18n marshrutini qo'shing
urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),  
]
