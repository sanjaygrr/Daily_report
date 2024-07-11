from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from registros import views as registros_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', registros_views.home, name='home'),
    path('registros/', include('registros.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
