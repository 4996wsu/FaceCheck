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
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/done/', views.CustomPasswordResetComplete.as_view(), name='password_done'),
   
    ]

urlpatterns += staticfiles_urlpatterns()