from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('',views.home, name= 'home'),
    path('home', views.home, name= 'home'),
    path('stats', views.stats, name= 'stats'),
    path('sign-up', views.sign_up, name= 'sign_up'),
    path('logout/', LogoutView.as_view(next_page='/home'), name='logout'),
     path('otp-verification/', views.otp_verification, name='otp_verification')
]

urlpatterns += staticfiles_urlpatterns()