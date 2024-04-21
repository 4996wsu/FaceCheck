from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

#this are urls for the webapp
urlpatterns = [
    path('',views.home, name= 'home'),
    path('home', views.home, name= 'home'),#this is the home page
    path('stats', views.stats, name= 'stats'),#this is the stats page
    path('manageclass', views.manageclass, name= 'manageclass'),#this is the manage class page
    path('sign-up', views.sign_up, name= 'sign_up'),#this is the sign up page
    path('enroll',views.enroll, name= 'enroll'),#this is the photo page
    path('logout/', LogoutView.as_view(next_page='/home'), name='logout'),
    path('otp-verification/', views.otp_verification, name='otp_verification'),#this is the otp verification page
    path('verify_otp/', views.otp_verification, name='verify_otp'), #this is the verify otp page
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),#this is the password reset page
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),#this is the password reset done page
   path('reset/done/', views.CustomPasswordResetComplete.as_view(), name='password_done'),  # Corrected view name
]
#this is the url for the static files
urlpatterns += staticfiles_urlpatterns()