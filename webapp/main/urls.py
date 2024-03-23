from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('',views.home, name= 'home'),
    path('home', views.home, name= 'home'),
    path('stats', views.stats, name= 'stats'),
    path('manageclass', views.manageclass, name= 'manageclass'),
    path('sign-up', views.sign_up, name= 'sign_up'),
    path('enroll',views.enroll, name= 'enroll'),
    path('logout/', LogoutView.as_view(next_page='/home'), name='logout'),
    path('otp-verification/', views.otp_verification, name='otp_verification'),
    path('verify_otp/', views.otp_verification, name='verify_otp'), 
    path('password_reset/', views.ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view, name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view, name='password_reset_complete'),
]

urlpatterns += staticfiles_urlpatterns()