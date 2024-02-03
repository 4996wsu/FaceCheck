from django import path
from . import views

urlpatterns = [
    path('',views.home, name= 'home'),
    path('home', views.home, name= 'home')
    path('stats', views.stats, name = 'stats'),
    path('sign-up', views.sign_up, name= 'sign_up'),
    ]