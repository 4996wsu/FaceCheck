from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('',views.home, name= 'home'),
    path('home', views.home, name= 'home'),
    path('stats', views.stats, name= 'stats'),
    path('sign-up', views.sign_up, name= 'sign_up'),
    path('enroll',views.enroll, name= 'enroll'),
]

urlpatterns += staticfiles_urlpatterns()