from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from registros import views as registros_views
from registros.forms import CustomPasswordResetForm
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', registros_views.landing_page, name='landing_page'),
    path('registros/', include('registros.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', form_class=CustomPasswordResetForm), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Opcional: también servir archivos estáticos desde STATIC_ROOT en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
